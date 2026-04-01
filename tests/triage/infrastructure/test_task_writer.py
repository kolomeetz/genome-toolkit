from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from genome_toolkit.triage.domain.commands import (
    ApproveCommand,
    ChangePriorityCommand,
    CreateCommand,
    DeferCommand,
    DropCommand,
)
from genome_toolkit.triage.domain.item import Context, ItemId, Priority
from genome_toolkit.triage.infrastructure.vault.task_writer import TaskWriter


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.fixture
def writer(vault_copy: Path) -> TaskWriter:
    return TaskWriter(vault_root=vault_copy)


def test_updates_inline_fields_and_completion(writer: TaskWriter, vault_copy: Path) -> None:
    file_path = vault_copy / "Reports" / "Prescriber Summary.md"
    item_id = ItemId.from_block_id("task-nortriptyline")

    writer.apply_command(
        ApproveCommand(item_id=item_id)
    )

    content = _read(file_path)
    assert "- [x] Discuss nortriptyline" in content


def test_updates_item_without_block_id(writer: TaskWriter, vault_copy: Path) -> None:
    file_path = vault_copy / "Genes" / "IL1B.md"
    item_id = ItemId.from_content(
        "IL1B",
        "Incorporate SSRI non-remission finding from research",
    )

    writer.apply_command(DeferCommand(item_id=item_id, days=7))

    content = _read(file_path)
    assert "[due::" in content  # defer updated the due date


def test_drop_marks_completed(writer: TaskWriter, vault_copy: Path) -> None:
    file_path = vault_copy / "Research" / "20260327-sample-research.md"
    item_id = ItemId.from_block_id("task-il6-ibs")

    writer.apply_command(DropCommand(item_id=item_id, note="not relevant"))
    assert "- [x] Check if [[IL6]]" in _read(file_path)


def test_create_new_item(writer: TaskWriter, vault_copy: Path) -> None:
    file_path = vault_copy / "Research" / "20260327-sample-research.md"
    command = CreateCommand(
        file_path=file_path,
        text="Follow up with prescriber",
        priority=Priority.HIGH,
        context=Context.PRESCRIBER,
        due=date(2026, 4, 2),
    )

    writer.create_item(command)
    content = _read(file_path)
    assert "Follow up with prescriber" in content
    assert "[priority:: high]" in content
    assert "[context:: prescriber]" in content
    assert "[due:: 2026-04-02]" in content
