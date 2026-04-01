"""TaskRepository implementation: parse Obsidian vault tasks into TriageItems."""
from __future__ import annotations

import fcntl
import re
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Generator, Union

import frontmatter

from genome_toolkit.triage.domain.commands import (
    ApproveCommand,
    ChangePriorityCommand,
    CreateCommand,
    DeferCommand,
    DropCommand,
)
from genome_toolkit.triage.domain.item import (
    Context,
    EvidenceTier,
    ItemId,
    Priority,
    SourceLocation,
    TriageItem,
)
from genome_toolkit.triage.domain.ports.repositories import TaskRepository

# Regex for checklist items: - [ ] or - [x]
_TASK_RE = re.compile(r"^- \[([ xX])\] (.+)$")

# Dataview inline field: [key:: value]
_INLINE_FIELD_RE = re.compile(r"\[([a-zA-Z_][\w]*?)::\s*(.+?)\]")

# Obsidian block id: ^block-id (may appear mid-line before inline fields)
_BLOCK_ID_RE = re.compile(r"\^([\w-]+)")

# Wikilink in task text: [[Target]] or [[Target|Alias]]
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*?)?(?:\|[^\]]*?)?\]\]")

# Directories to skip when scanning vault
_EXCLUDE_DIRS = {"Templates", "data", ".obsidian", ".trash", ".claude", "Guides"}

_PRIORITY_MAP = {
    "critical": Priority.CRITICAL,
    "high": Priority.HIGH,
    "medium": Priority.MEDIUM,
    "low": Priority.LOW,
}

_CONTEXT_MAP = {
    "prescriber": Context.PRESCRIBER,
    "testing": Context.TESTING,
    "monitoring": Context.MONITORING,
    "research": Context.RESEARCH,
    "vault-maintenance": Context.VAULT_MAINTENANCE,
}

_EVIDENCE_MAP = {
    "E1": EvidenceTier.E1,
    "E2": EvidenceTier.E2,
    "E3": EvidenceTier.E3,
    "E4": EvidenceTier.E4,
    "E5": EvidenceTier.E5,
}


class VaultTaskRepository(TaskRepository):
    def __init__(self, vault_path: Path) -> None:
        self._vault_path = vault_path
        self._gene_tier_cache: dict[str, EvidenceTier | None] | None = None

    def _get_gene_tier_cache(self) -> dict[str, EvidenceTier | None]:
        """Build a cache of gene_symbol -> evidence_tier from Genes/ directory."""
        if self._gene_tier_cache is not None:
            return self._gene_tier_cache

        cache: dict[str, EvidenceTier | None] = {}
        gene_dir = self._vault_path / "Genes"
        if gene_dir.exists():
            for gene_file in gene_dir.glob("*.md"):
                try:
                    post = frontmatter.load(str(gene_file))
                    meta = dict(post.metadata) if post.metadata else {}
                except Exception:
                    continue
                symbol = meta.get("gene_symbol", gene_file.stem)
                tier = self._parse_evidence_tier(meta.get("evidence_tier"))
                cache[str(symbol)] = tier

        self._gene_tier_cache = cache
        return cache

    def _resolve_evidence_tier(
        self,
        note_tier: EvidenceTier | None,
        linked_genes: list[str],
    ) -> EvidenceTier | None:
        """Return note-level tier if present, else highest tier from linked genes."""
        if note_tier is not None:
            return note_tier

        gene_cache = self._get_gene_tier_cache()
        tiers = [
            gene_cache[g] for g in linked_genes
            if g in gene_cache and gene_cache[g] is not None
        ]
        if not tiers:
            return None
        # Return the highest evidence tier (highest IntEnum value = most reliable)
        return max(tiers)

    def get_all_open(self) -> list[TriageItem]:
        items: list[TriageItem] = []
        for md_file in sorted(self._vault_path.rglob("*.md")):
            rel = md_file.relative_to(self._vault_path)
            if any(part in _EXCLUDE_DIRS for part in rel.parts):
                continue
            items.extend(self._parse_file(md_file))
        return items

    def _parse_file(self, file_path: Path) -> list[TriageItem]:
        """Parse all open tasks from a single markdown file."""
        try:
            post = frontmatter.load(str(file_path))
            meta = dict(post.metadata) if post.metadata else {}
        except Exception:
            meta = {}

        text = file_path.read_text(encoding="utf-8")
        lines = text.splitlines()

        # Extract note-level metadata
        note_evidence_tier = self._parse_evidence_tier(meta.get("evidence_tier"))
        note_genes = self._extract_genes_from_frontmatter(meta)
        note_systems = self._extract_systems_from_frontmatter(meta)

        items: list[TriageItem] = []
        for line_num_0, line in enumerate(lines):
            line_number = line_num_0 + 1  # 1-based
            m = _TASK_RE.match(line.strip())
            if not m:
                continue

            completed = m.group(1).lower() == "x"
            if completed:
                continue

            raw_text = m.group(2)

            # Extract inline fields
            fields = dict(_INLINE_FIELD_RE.findall(raw_text))

            # Extract block id
            block_id_match = _BLOCK_ID_RE.search(raw_text)
            block_id = block_id_match.group(1) if block_id_match else None

            # Clean task text: remove inline fields and block id
            task_text = _INLINE_FIELD_RE.sub("", raw_text)
            task_text = _BLOCK_ID_RE.sub("", task_text)
            task_text = task_text.strip().rstrip("—").rstrip("-").strip()

            # Extract wikilinks from task text for gene linking
            task_wikilinks = _WIKILINK_RE.findall(raw_text)

            # Build linked genes: from frontmatter + from task wikilinks to Genes/
            linked_genes = list(note_genes)
            for link_target in task_wikilinks:
                # Check if it's a gene reference (exists in Genes/ or looks like a gene symbol)
                if self._is_gene_reference(link_target):
                    if link_target not in linked_genes:
                        linked_genes.append(link_target)

            # Build item_id
            if block_id:
                item_id = ItemId.from_block_id(block_id)
            else:
                item_id = ItemId.from_content(file_path.stem, task_text)

            # Parse fields
            priority = _PRIORITY_MAP.get(
                fields.get("priority", "").lower(), Priority.MEDIUM
            )
            context = _CONTEXT_MAP.get(
                fields.get("context", "").lower(), Context.RESEARCH
            )
            due = self._parse_due(fields.get("due"))

            # Resolve evidence tier: parent note first, then linked genes
            resolved_tier = self._resolve_evidence_tier(
                note_evidence_tier, linked_genes
            )

            items.append(TriageItem(
                item_id=item_id,
                source=SourceLocation(
                    file_path=file_path,
                    line_number=line_number,
                ),
                text=task_text,
                priority=priority,
                context=context,
                due=due,
                completed=False,
                evidence_tier=resolved_tier,
                severity=None,
                linked_genes=linked_genes,
                linked_systems=list(note_systems),
            ))

        return items

    def _is_gene_reference(self, target: str) -> bool:
        """Check if a wikilink target refers to a gene."""
        gene_dir = self._vault_path / "Genes"
        if gene_dir.exists():
            gene_file = gene_dir / f"{target}.md"
            if gene_file.exists():
                return True
        # Heuristic: all-caps or CamelCase gene symbols
        return bool(re.match(r"^[A-Z][A-Z0-9]+$", target))

    @staticmethod
    def _parse_evidence_tier(raw: str | None) -> EvidenceTier | None:
        if raw is None:
            return None
        return _EVIDENCE_MAP.get(str(raw).strip())

    @staticmethod
    def _extract_genes_from_frontmatter(meta: dict) -> list[str]:
        genes = meta.get("genes", [])
        if isinstance(genes, str):
            genes = [genes]
        if not isinstance(genes, list):
            return []
        return [str(g) for g in genes]

    @staticmethod
    def _extract_systems_from_frontmatter(meta: dict) -> list[str]:
        systems = meta.get("systems", [])
        if isinstance(systems, str):
            systems = [systems]
        if not isinstance(systems, list):
            return []
        return [str(s) for s in systems]

    @staticmethod
    def _parse_due(raw: str | None) -> date | None:
        if not raw:
            return None
        raw = raw.strip()
        try:
            parts = raw.split("-")
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            return None

    def apply_command(
        self,
        command: Union[DeferCommand, ApproveCommand, DropCommand, ChangePriorityCommand],
    ) -> None:
        # Delegate to TaskWriter (separate concern)
        from genome_toolkit.triage.infrastructure.vault.task_writer import TaskWriter
        writer = TaskWriter(self._vault_path)
        writer.apply_command(command)

    def create_item(self, command: CreateCommand) -> None:
        from genome_toolkit.triage.infrastructure.vault.task_writer import TaskWriter
        writer = TaskWriter(self._vault_path)
        writer.create_item(command)

    @contextmanager
    def acquire_lock(self) -> Generator[None, None, None]:
        lock_path = self._vault_path / ".triage.lock"
        lock_file = open(lock_path, "w")
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        except OSError as e:
            lock_file.close()
            raise RuntimeError("Another triage session is active") from e
        finally:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            finally:
                lock_file.close()
                try:
                    lock_path.unlink()
                except FileNotFoundError:
                    pass
