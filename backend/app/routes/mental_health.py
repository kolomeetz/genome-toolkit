"""Mental health dashboard API — reads vault notes, returns structured dashboard data."""
from pathlib import Path

from fastapi import APIRouter

from backend.app.agent import tools as _tools
from backend.app.vault_parser import parse_gene_note

router = APIRouter(prefix="/api/mental-health")


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


# Mental health pathways — which genes belong to which pathway
PATHWAYS = {
    'Methylation Pathway': ['MTHFR', 'MTRR', 'MTR'],
    'Serotonin & Neuroplasticity': ['SLC6A4', 'BDNF', 'HTR2A', 'TPH2'],
    'Dopamine & Reward': ['COMT', 'DRD2', 'DRD4', 'SLC6A3'],
    'Monoamine Regulation': ['MAO-A', 'FKBP5'],
    'GABA & Sleep': ['GAD1', 'GABRA2'],
}

STATUS_PRIORITIES: dict[str, int] = {'actionable': 0, 'monitor': 1, 'neutral': 2, 'optimal': 3}


@router.get("/dashboard")
async def get_dashboard():
    """Return structured dashboard data parsed from vault notes."""
    sections = []

    for pathway_name, gene_symbols in PATHWAYS.items():
        genes = []
        all_actions: dict[str, list] = {}
        pathway_status = 'optimal'
        total_actions = 0

        for symbol in gene_symbols:
            note = _read_gene_note(symbol)
            if not note:
                continue

            parsed = parse_gene_note(note['content'])
            if not parsed['symbol']:
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

        # Build gene_meta (population info, explanation, interactions) in one pass
        gene_meta: dict[str, dict] = {}
        for g in genes:
            g_note = _read_gene_note(g['symbol'])
            if not g_note:
                gene_meta[g['symbol']] = {'populationInfo': '', 'explanation': '', 'interactions': []}
                continue
            p = parse_gene_note(g_note['content'])
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
    for s in sections:
        for g in s['genes']:
            g_note = _read_gene_note(g['symbol'])
            if g_note:
                p = parse_gene_note(g_note['content'])
                if p.get('last_reviewed'):
                    all_dates.append(p['last_reviewed'])

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
