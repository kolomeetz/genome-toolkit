"""Mental health dashboard API — reads vault notes, returns structured dashboard data.

Pathway definitions are loaded from config/pathway-systems.yaml (domain: mental-health).
Genes are matched by their vault `systems` frontmatter tags, not by hardcoded gene lists.
"""
import re
from pathlib import Path

import yaml
from fastapi import APIRouter

from backend.app.agent import tools as _tools
from backend.app.vault_parser import parse_gene_note

router = APIRouter(prefix="/api/mental-health")

_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"


def _normalize_gene_symbol(symbol: str) -> str:
    """Normalize gene symbol for file lookup: MAO-A -> MAOA, SLC6A3 -> SLC6A3."""
    return symbol.replace("-", "").upper()


def _read_gene_note(symbol: str) -> dict | None:
    if not _tools._vault_path:
        return None
    normalized = _normalize_gene_symbol(symbol)
    vault = _tools._vault_path
    gene_file = Path(vault) / "Genes" / f"{normalized}.md"
    if not gene_file.exists():
        gene_file = Path(vault) / "Genes" / f"{symbol}.md"
    if not gene_file.exists():
        genes_dir = Path(vault) / "Genes"
        if genes_dir.exists():
            for f in genes_dir.iterdir():
                if f.stem.upper().replace("-", "") == normalized:
                    gene_file = f
                    break
    if not gene_file.exists():
        return None
    content = gene_file.read_text()
    return {"symbol": symbol, "content": content}


def _load_mental_health_pathways() -> dict[str, list[str]]:
    """Load mental-health pathways from config/pathway-systems.yaml.

    Returns dict mapping pathway name -> list of vault system tags to match against.
    Falls back to hardcoded defaults if config is missing.
    """
    config_file = _CONFIG_DIR / "pathway-systems.yaml"
    if config_file.exists():
        data = yaml.safe_load(config_file.read_text()) or {}
        systems = data.get("systems", {})
        pathways: dict[str, list[str]] = {}
        for sys in systems.values():
            if "mental-health" in sys.get("domains", []):
                pathways[sys["name"]] = sys.get("tags", [])
        if pathways:
            return pathways

    # Fallback: original hardcoded pathways (tag-based, not gene-list)
    return {
        'Methylation Pathway': ['Methylation'],
        'Serotonin & Neuroplasticity': ['Serotonin System', 'Neurotransmitter Synthesis'],
        'Dopamine & Reward': ['Dopamine System', 'Behavioral Architecture'],
        'GABA & Sleep': ['GABA System', 'Sleep Architecture'],
        'Stress Response': ['Stress Response', 'HPA Axis'],
    }


def _strip_wikilinks(value: str) -> str:
    """Remove Obsidian wikilink brackets: '[[Foo]]' -> 'Foo'."""
    return re.sub(r"\[\[([^\]]+)\]\]", r"\1", value)


def _gene_matches_tags(gene_systems: list[str], pathway_tags: list[str]) -> bool:
    """Check if a gene's system tags match any of the pathway's tags."""
    lower_tags = [t.lower() for t in pathway_tags]
    for s in gene_systems:
        clean = _strip_wikilinks(s).split("|")[0].strip().lower()
        if any(tag in clean or clean in tag for tag in lower_tags):
            return True
    return False


STATUS_PRIORITIES: dict[str, int] = {'actionable': 0, 'monitor': 1, 'neutral': 2, 'optimal': 3}


@router.get("/dashboard")
async def get_dashboard():
    """Return structured dashboard data parsed from vault notes.

    Pathways loaded from config/pathway-systems.yaml (mental-health domain).
    Genes matched by vault systems tags, not hardcoded gene lists.
    """
    pathways = _load_mental_health_pathways()
    sections = []

    # First, scan all vault genes to build a pool we can match by system tags
    vault_genes_by_symbol: dict[str, dict] = {}
    if _tools._vault_path:
        genes_dir = Path(_tools._vault_path) / "Genes"
        if genes_dir.exists():
            for f in sorted(genes_dir.iterdir()):
                if f.suffix != ".md":
                    continue
                note_text = f.read_text()
                parsed = parse_gene_note(note_text)
                if not parsed.get("symbol"):
                    continue
                # Extract systems from frontmatter for tag matching
                if note_text.startswith("---"):
                    parts = note_text.split("---", 2)
                    if len(parts) >= 3:
                        fm = yaml.safe_load(parts[1]) or {}
                        raw_systems = fm.get("systems", [])
                        if isinstance(raw_systems, list):
                            parsed["_systems"] = [
                                _strip_wikilinks(s).split("|")[0].strip()
                                if isinstance(s, str) else str(s)
                                for s in raw_systems
                            ]
                        else:
                            parsed["_systems"] = []
                    else:
                        parsed["_systems"] = []
                else:
                    parsed["_systems"] = []
                vault_genes_by_symbol[parsed["symbol"]] = parsed

    for pathway_name, pathway_tags in pathways.items():
        genes = []
        all_actions: dict[str, list] = {}
        pathway_status = 'optimal'
        total_actions = 0

        # Match genes by system tags
        for symbol, parsed in vault_genes_by_symbol.items():
            if not _gene_matches_tags(parsed.get("_systems", []), pathway_tags):
                continue

            gene_data = {
                'symbol': parsed['symbol'],
                'variant': parsed['variant'],
                'rsid': parsed['rsid'],
                'genotype': parsed['genotype'],
                'status': parsed['status'],
                'evidenceTier': parsed['evidence_tier'],
                'studyCount': parsed['study_count'],
                'description': parsed['description'],
                'actionCount': len(parsed['actions']),
                'categories': parsed['categories'],
                'pathway': pathway_name,
            }
            genes.append(gene_data)

            # Collect actions
            action_list = []
            for i, a in enumerate(parsed['actions']):
                action_list.append({
                    'id': f"{parsed['symbol'].lower()}-{i}",
                    'type': a['type'],
                    'title': a['title'],
                    'description': a['description'],
                    'evidenceTier': parsed['evidence_tier'],
                    'studyCount': parsed['study_count'],
                    'tags': [a.get('practical_category', '')],
                    'geneSymbol': parsed['symbol'],
                    'done': False,
                })
            if action_list:
                all_actions[parsed['symbol']] = action_list
                total_actions += len(action_list)

            # Track worst status for pathway narrative
            if STATUS_PRIORITIES.get(parsed['status'], 3) < STATUS_PRIORITIES.get(pathway_status, 3):
                pathway_status = parsed['status']

        if not genes:
            continue

        # Build narrative from gene data
        gene_names = ', '.join(g['symbol'] for g in genes)
        status_text = {
            'actionable': f'Your {pathway_name.lower()} shows variants that benefit from targeted intervention.',
            'monitor': f'Your {pathway_name.lower()} shows moderate variants worth monitoring.',
            'optimal': f'Your {pathway_name.lower()} is in the optimal range — protective factors present.',
            'neutral': f'Your {pathway_name.lower()} shows no clinically significant variants.',
        }

        # Build gene_meta (population info, explanation, interactions)
        gene_meta: dict[str, dict] = {}
        for g in genes:
            p = vault_genes_by_symbol.get(g['symbol'], {})
            gene_meta[g['symbol']] = {
                'populationInfo': p.get('population_info', ''),
                'explanation': p.get('explanation', ''),
                'interactions': p.get('interactions', []),
            }

        sections.append({
            'narrative': {
                'pathway': pathway_name,
                'status': pathway_status,
                'body': status_text.get(pathway_status, ''),
                'priority': f'Status: {pathway_status}',
                'hint': gene_names,
                'geneCount': len(genes),
                'actionCount': total_actions,
            },
            'genes': genes,
            'actions': all_actions,
            'gene_meta': gene_meta,
        })

    total_genes = sum(len(s['genes']) for s in sections)
    total_actions_all = sum(s['narrative']['actionCount'] for s in sections)

    # Find most recent review date across all genes
    all_dates = []
    for parsed in vault_genes_by_symbol.values():
        if parsed.get('last_reviewed'):
            all_dates.append(parsed['last_reviewed'])

    return {
        'sections': sections,
        'totalGenes': total_genes,
        'totalActions': total_actions_all,
        'lastUpdated': max(all_dates, default=''),
    }


@router.get("/genes")
async def list_mental_health_genes():
    mh_genes = [
        "MTHFR", "COMT", "MAO-A", "SLC6A4", "BDNF",
        "GAD1", "CRHR1", "FKBP5", "TPH2", "HTR2A",
        "DRD2", "DRD4", "OPRM1", "GABRA2", "SLC6A3",
    ]
    result = []
    for symbol in mh_genes:
        note = _read_gene_note(symbol)
        result.append({"symbol": symbol, "has_vault_note": note is not None})
    return {"genes": result}


@router.get("/genes/{symbol}")
async def get_gene_detail(symbol: str):
    note = _read_gene_note(symbol.upper())
    if not note:
        return {"error": f"No vault note found for {symbol}"}
    return note
