"""Parse Obsidian vault gene notes into structured data for the API."""
import re
from pathlib import Path
from typing import Any

import yaml


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from markdown."""
    if not content.startswith('---'):
        return {}, content
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}
    body = parts[2].strip()
    return meta, body


def extract_section(body: str, heading: str) -> str:
    """Extract content under a specific ## heading."""
    pattern = rf'^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)'
    match = re.search(pattern, body, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ''


def parse_gene_note(content: str) -> dict[str, Any]:
    """Parse a vault gene note into structured data.

    Returns dict with: symbol, full_name, chromosome, genotype, rsid,
    status, evidence_tier, description, variants, actions, interactions,
    population_info, explanation, systems, tags
    """
    meta, body = parse_frontmatter(content)

    # Map personal_status to our GeneStatus type
    status_map = {
        'risk': 'actionable',
        'actionable': 'actionable',
        'intermediate': 'monitor',
        'monitor': 'monitor',
        'neutral': 'neutral',
        'optimal': 'optimal',
        'protective': 'optimal',
        'normal': 'optimal',
        'typical': 'optimal',
    }

    # Extract variants
    variants = meta.get('personal_variants', [])
    primary_variant = variants[0] if variants else {}

    # Extract genotype - clean up the format
    raw_genotype = primary_variant.get('genotype', '')
    # Parse "G;T (= A;C on + strand, A1298C heterozygous)" -> "G/T"
    clean_genotype = raw_genotype.split('(')[0].strip().replace(';', '/')

    # Extract rsid
    rsid = primary_variant.get('rsid', '')

    # Extract variant name from significance or rsid
    variant_name = ''
    for v in variants:
        sig = v.get('significance', '')
        # Look for patterns like "C677T" or "A1298C" in significance
        match = re.search(r'([A-Z]\d+[A-Z])', sig)
        if match:
            variant_name = match.group(1)
            break
    if not variant_name and rsid:
        variant_name = rsid

    # Map evidence tier
    tier = meta.get('evidence_tier', 'E5')
    if isinstance(tier, str) and not tier.startswith('E'):
        tier = 'E3'  # default moderate

    # Extract "What Changes This" section for actions
    actions_text = (
        extract_section(body, 'What Changes This')
        or extract_section(body, 'What To Do')
        or extract_section(body, 'Actionable Recommendations')
    )
    actions = []
    if actions_text:
        for line in actions_text.split('\n'):
            line = line.strip()
            if line.startswith('- **') or line.startswith('- '):
                # Parse "- **Methylfolate (L-5-MTHF) 400-800mcg/day**: Description"
                clean = line.lstrip('- ').strip()
                if '**:' in clean or '**: ' in clean:
                    parts = clean.split('**', 2)
                    if len(parts) >= 3:
                        title = parts[1].strip(':').strip()
                        desc = parts[2].strip(':').strip()
                        # Determine action type from content
                        action_type = 'consider'
                        lower = (title + desc).lower()
                        if any(w in lower for w in ['test', 'measure', 'check', 'monitor', 'blood']):
                            action_type = 'monitor'
                        elif any(w in lower for w in ['discuss', 'ask', 'clinician', 'doctor']):
                            action_type = 'discuss'
                        elif any(w in lower for w in ['exercise', 'meditation', 'walk', 'sleep', 'avoid']):
                            action_type = 'try'

                        # Determine practical category
                        practical = 'research'
                        if any(w in lower for w in ['supplement', 'mcg', 'mg', 'take', 'capsule']):
                            practical = 'buy'
                        elif any(w in lower for w in ['test', 'blood', 'measure']):
                            practical = 'test'
                        elif any(w in lower for w in ['exercise', 'meditation', 'walk', 'sleep', 'avoid', 'reduce']):
                            practical = 'practice'

                        actions.append({
                            'title': title,
                            'description': desc,
                            'type': action_type,
                            'practical_category': practical,
                        })

    # Extract gene-gene interactions
    interactions_text = (
        extract_section(body, 'Gene-Gene Interactions')
        or extract_section(body, 'Gene Interactions')
    )
    interactions = []
    if interactions_text:
        for line in interactions_text.split('\n'):
            line = line.strip()
            if line.startswith('- **'):
                parts = line.lstrip('- ').split('**', 2)
                if len(parts) >= 3:
                    genes = parts[1].strip(':').strip()
                    desc = parts[2].strip(':').strip()
                    interactions.append({'genes': genes, 'description': desc})

    # Extract explanation from "What This Gene Does" or "Health Relevance"
    explanation = (
        extract_section(body, 'What This Gene Does')
        or extract_section(body, 'Health Relevance')
    )
    # Trim to first paragraph
    if explanation:
        paragraphs = [p.strip() for p in explanation.split('\n\n') if p.strip() and not p.strip().startswith('#')]
        explanation = paragraphs[0] if paragraphs else ''

    # Extract "Status" line from Personal Genotype section
    personal_section = extract_section(body, 'Personal Genotype')
    population_info = ''
    if personal_section:
        for line in personal_section.split('\n'):
            if line.startswith('**Status:**') or line.startswith('**Metabolizer status:**'):
                population_info = re.sub(r'^\*\*[^*]+\*\*:?\s*', '', line).strip()
                break

    # Systems/categories
    systems = meta.get('systems', [])
    categories = []
    system_to_category = {
        'methylation': 'mood',
        'serotonin': 'mood',
        'dopamine': 'focus',
        'gaba': 'sleep',
        'sleep': 'sleep',
        'stress': 'stress',
        'reward': 'focus',
    }
    for s in systems:
        s_lower = s.lower().replace('[[', '').replace(']]', '')
        for key, cat in system_to_category.items():
            if key in s_lower and cat not in categories:
                categories.append(cat)
    if not categories:
        categories = ['mood']  # default

    # Count studies from sources section
    sources_text = extract_section(body, 'Sources')
    study_count = len([l for l in sources_text.split('\n') if l.strip().startswith('-')]) if sources_text else 0

    return {
        'symbol': meta.get('gene_symbol', ''),
        'full_name': meta.get('full_name', ''),
        'chromosome': meta.get('chromosome', ''),
        'variant': variant_name,
        'rsid': rsid,
        'genotype': clean_genotype,
        'status': status_map.get(meta.get('personal_status', 'neutral'), 'neutral'),
        'evidence_tier': tier,
        'study_count': max(study_count, 1),
        'description': meta.get('description', ''),
        'personal_status': meta.get('personal_status', ''),
        'variants': variants,
        'actions': actions,
        'interactions': interactions,
        'explanation': explanation,
        'population_info': population_info,
        'categories': categories,
        'systems': systems,
        'tags': meta.get('tags', []),
        'last_reviewed': str(meta.get('last_reviewed', '')),
    }
