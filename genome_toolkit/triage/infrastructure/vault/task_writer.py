"""TaskWriter: writes priority/due/completed changes back to .md files.

Stub implementation — full implementation is outside current scope.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Union

from genome_toolkit.triage.domain.commands import (
    ApproveCommand,
    ChangePriorityCommand,
    CreateCommand,
    DeferCommand,
    DropCommand,
)
from genome_toolkit.triage.domain.item import ItemId

import re

_TASK_RE = re.compile(r"^(- \[)([ xX])(\] .+)$")
_BLOCK_ID_RE = re.compile(r"\^([\w-]+)")
_INLINE_FIELD_RE = re.compile(r"\[([a-zA-Z_][\w]*?)::\s*(.+?)\]")


class TaskWriter:
    def __init__(self, vault_root: Path) -> None:
        self._vault_root = vault_root

    def apply_command(
        self,
        command: Union[DeferCommand, ApproveCommand, DropCommand, ChangePriorityCommand],
    ) -> None:
        file_path, line_idx = self._find_item(command.item_id)
        if file_path is None:
            raise ValueError(f"Item {command.item_id.value} not found")

        lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
        line = lines[line_idx]

        if isinstance(command, ApproveCommand):
            line = line.replace("- [ ]", "- [x]", 1)
        elif isinstance(command, DropCommand):
            line = line.replace("- [ ]", "- [x]", 1)
        elif isinstance(command, ChangePriorityCommand):
            new_p = command.new_priority.name.lower()
            line = _INLINE_FIELD_RE.sub(
                lambda m: f"[priority:: {new_p}]" if m.group(1) == "priority" else m.group(0),
                line,
            )
        elif isinstance(command, DeferCommand):
            today = date.today()
            new_due = today + timedelta(days=command.days)
            due_str = new_due.isoformat()
            if "[due::" in line:
                line = _INLINE_FIELD_RE.sub(
                    lambda m: f"[due:: {due_str}]" if m.group(1) == "due" else m.group(0),
                    line,
                )
            else:
                # Add due field before any trailing block id or newline
                line = line.rstrip("\n").rstrip()
                line += f" [due:: {due_str}]\n"

        lines[line_idx] = line
        file_path.write_text("".join(lines), encoding="utf-8")

    def create_item(self, command: CreateCommand) -> None:
        file_path = command.file_path
        content = file_path.read_text(encoding="utf-8")

        parts = [f"- [ ] {command.text}"]
        parts.append(f"[priority:: {command.priority.name.lower()}]")
        parts.append(f"[context:: {command.context.name.lower().replace('_', '-')}]")
        if command.due:
            parts.append(f"[due:: {command.due.isoformat()}]")

        new_line = " ".join(parts) + "\n"
        content = content.rstrip("\n") + "\n" + new_line
        file_path.write_text(content, encoding="utf-8")

    def _find_item(self, item_id: ItemId) -> tuple[Path | None, int]:
        """Find the file and line index for an item by its ItemId.

        Searches first by ^block-id, then by content hash match.
        """
        import hashlib

        for md_file in self._vault_root.rglob("*.md"):
            lines = md_file.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines):
                task_m = _TASK_RE.match(line.strip())
                if not task_m:
                    continue

                raw_text = task_m.group(3)[2:]  # strip leading "] "

                # Check block id match
                m = _BLOCK_ID_RE.search(raw_text)
                if m and m.group(1) == item_id.value:
                    return md_file, i

                # Check content hash match
                task_text = _INLINE_FIELD_RE.sub("", raw_text)
                task_text = _BLOCK_ID_RE.sub("", task_text)
                task_text = task_text.strip().rstrip("—").rstrip("-").strip()
                content_hash = hashlib.sha256(
                    f"{md_file.stem}|{task_text}".encode()
                ).hexdigest()
                if content_hash == item_id.value:
                    return md_file, i

        return None, -1
