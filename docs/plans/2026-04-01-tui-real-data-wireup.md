# TUI Real Data Wireup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all TUI stub data with live vault data via the application layer, making every button and action functional — approve creates tasks, defer updates due dates, drop marks completed, and all changes persist to vault markdown files.

**Architecture:** TriageApp receives a `vault_path` at construction time. On mount, it runs `RunTriageSession` to get real `TriageReport`. Each screen consumes real `ScoredItem` / `Suggestion` objects. Actions call `ApplyDecisions` to write back to vault. History reads from `Meta/Triage History.md`.

**Tech Stack:** Textual, existing domain/application/infrastructure layers, python-frontmatter

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `presentation/tui/app.py` | Modify | Accept vault_path, build repos, run use case, pass data to screens |
| `presentation/tui/data_bridge.py` | Create | Convert domain `ScoredItem`/`Suggestion` → `ScoredItemStub` (adapter) |
| `presentation/tui/screens/urgency.py` | Modify | Accept items from app instead of calling `make_sample_items()` |
| `presentation/tui/screens/context.py` | Modify | Accept items from app |
| `presentation/tui/screens/suggestions.py` | Modify | Accept suggestions from app, Approve actually creates task |
| `presentation/tui/screens/history.py` | Modify | Read real history from SessionRepository |
| `presentation/tui/widgets/item_card.py` | Modify | Visual feedback on actions (strikethrough, color change) |
| `presentation/tui/widgets/batch_bar.py` | Modify | Apply calls `ApplyDecisions`, discard reverts in-memory |
| `presentation/cli.py` | Modify | Pass vault_path to TriageApp |
| `tests/triage/presentation/test_tui.py` | Modify | Update tests for new constructor |

---

### Task 1: Data Bridge — convert domain types to TUI types

**Files:**
- Create: `genome_toolkit/triage/presentation/tui/data_bridge.py`
- Test: `tests/triage/presentation/test_data_bridge.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/triage/presentation/test_data_bridge.py
from __future__ import annotations
from datetime import date
from pathlib import Path
import pytest

from genome_toolkit.triage.domain.item import (
    ItemId, SourceLocation, TriageItem, Priority, Context, EvidenceTier, Severity,
)
from genome_toolkit.triage.domain.score import Score, ScoreBreakdown, TriageBucket
from genome_toolkit.triage.domain.suggestion import Suggestion, SuggestionSource
from genome_toolkit.triage.application.report import ScoredItem


def test_scored_item_to_stub():
    from genome_toolkit.triage.presentation.tui.data_bridge import scored_item_to_stub

    item = TriageItem(
        item_id=ItemId.from_content("test", "Request CRP blood test"),
        source=SourceLocation(file_path=Path("Reports/Prescriber Summary.md"), line_number=10),
        text="Request CRP blood test from prescriber",
        priority=Priority.CRITICAL,
        context=Context.PRESCRIBER,
        due=date(2026, 4, 15),
        completed=False,
        evidence_tier=EvidenceTier.E1,
        severity=Severity.SIGNIFICANT,
        linked_genes=["IL1B", "IL6"],
        linked_systems=["Immune"],
        blocked_by=[],
        clinically_validated=False,
    )
    breakdown = ScoreBreakdown(
        priority_score=25.0, overdue_score=15.0, evidence_score=15.0,
        lab_signal_score=12.0, context_score=10.0, severity_score=7.5, stuck_score=0.0,
    )
    score = Score(value=84.5, breakdown=breakdown, bucket=TriageBucket.DO_NOW)
    scored = ScoredItem(item=item, score=score)

    stub = scored_item_to_stub(scored)

    assert stub.text == "Request CRP blood test from prescriber"
    assert stub.score == 84.5
    assert stub.bucket == "DO_NOW"
    assert stub.priority == "critical"
    assert stub.context == "prescriber"
    assert stub.due == date(2026, 4, 15)
    assert stub.evidence_tier == "E1"
    assert stub.source_file == "Reports/Prescriber Summary.md"
    assert stub.linked_genes == ["IL1B", "IL6"]
    assert stub.breakdown["priority"] == 25.0


def test_suggestion_to_stub():
    from genome_toolkit.triage.presentation.tui.data_bridge import suggestion_to_stub

    suggestion = Suggestion(
        text="Update FADS1 gene note",
        source_type=SuggestionSource.UNINCORPORATED_FINDING,
        source_reference="Findings Index",
        recommended_priority=Priority.HIGH,
        recommended_context=Context.VAULT_MAINTENANCE,
        rationale="Finding not incorporated since 2026-03-25",
    )

    stub = suggestion_to_stub(suggestion)

    assert stub.text == "Update FADS1 gene note"
    assert stub.priority == "high"
    assert stub.context == "vault-maintenance"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /path/to/genome-toolkit && python -m pytest tests/triage/presentation/test_data_bridge.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'genome_toolkit.triage.presentation.tui.data_bridge'`

- [ ] **Step 3: Write implementation**

```python
# genome_toolkit/triage/presentation/tui/data_bridge.py
"""Convert domain types to TUI stub types for rendering."""
from __future__ import annotations

from genome_toolkit.triage.application.report import ScoredItem
from genome_toolkit.triage.domain.suggestion import Suggestion
from genome_toolkit.triage.presentation.tui.stub_data import ScoredItemStub


def scored_item_to_stub(scored: ScoredItem) -> ScoredItemStub:
    """Convert a domain ScoredItem to a TUI-renderable ScoredItemStub."""
    item = scored.item
    score = scored.score
    return ScoredItemStub(
        text=item.text,
        score=score.value,
        bucket=score.bucket.name,
        priority=item.priority.name.lower() if item.priority else "unknown",
        context=item.context.name.lower().replace("_", "-") if item.context else "unknown",
        due=item.due,
        evidence_tier=item.evidence_tier.name if item.evidence_tier else None,
        severity=item.severity.name.lower() if item.severity else None,
        linked_genes=list(item.linked_genes),
        lab_signal=None,
        breakdown={
            "priority": score.breakdown.priority_score,
            "overdue": score.breakdown.overdue_score,
            "evidence": score.breakdown.evidence_score,
            "lab_signal": score.breakdown.lab_signal_score,
            "context": score.breakdown.context_score,
            "severity": score.breakdown.severity_score,
            "stuck": score.breakdown.stuck_score,
        },
        clinically_validated=item.clinically_validated,
        blocked_by=[bid.value for bid in item.blocked_by],
        source_file=str(item.source.file_path),
    )


def suggestion_to_stub(suggestion: Suggestion) -> ScoredItemStub:
    """Convert a domain Suggestion to a TUI-renderable ScoredItemStub."""
    return ScoredItemStub(
        text=suggestion.text,
        score=0.0,
        bucket="SUGGESTED",
        priority=suggestion.recommended_priority.name.lower(),
        context=suggestion.recommended_context.name.lower().replace("_", "-"),
        evidence_tier=None,
        linked_genes=[],
        source_file=suggestion.source_reference,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /path/to/genome-toolkit && python -m pytest tests/triage/presentation/test_data_bridge.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add genome_toolkit/triage/presentation/tui/data_bridge.py tests/triage/presentation/test_data_bridge.py
git commit -m "feat(triage): add data bridge converting domain types to TUI stubs"
```

---

### Task 2: TriageApp accepts vault_path and loads real data

**Files:**
- Modify: `genome_toolkit/triage/presentation/tui/app.py`
- Modify: `genome_toolkit/triage/presentation/cli.py`

- [ ] **Step 1: Modify TriageApp to accept vault_path and build report on mount**

```python
# genome_toolkit/triage/presentation/tui/app.py — full replacement
"""Main Textual App for the Triage TUI dashboard."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane

from genome_toolkit.triage.application.report import TriageReport
from genome_toolkit.triage.presentation.tui.screens.urgency import UrgencyScreen
from genome_toolkit.triage.presentation.tui.screens.context import ContextScreen
from genome_toolkit.triage.presentation.tui.screens.suggestions import SuggestionsScreen
from genome_toolkit.triage.presentation.tui.screens.history import HistoryScreen
from genome_toolkit.triage.presentation.tui.widgets.batch_bar import BatchBar
from genome_toolkit.triage.presentation.tui.widgets.item_card import ItemCard
from genome_toolkit.triage.presentation.tui.stub_data import ScoredItemStub


class TriageApp(App):
    """Genome Triage TUI dashboard with 4 tabs."""

    TITLE = "Genome Triage"
    CSS_PATH = "triage.tcss"

    BINDINGS = [
        ("q", "quit_app", "Quit"),
        ("s", "save_svg", "Save SVG"),
        ("slash", "search", "Search"),
    ]

    def __init__(self, vault_path: Optional[Path] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._vault_path = vault_path
        self._report: Optional[TriageReport] = None
        self._items: list[ScoredItemStub] = []
        self._suggestions: list[ScoredItemStub] = []
        self._pending_actions: list[tuple] = []  # (item, command) pairs

    def on_mount(self) -> None:
        """Load real data on mount if vault_path provided."""
        if self._vault_path:
            self._load_real_data()

    def _load_real_data(self) -> None:
        """Run triage use case and convert to TUI types."""
        from genome_toolkit.triage.infrastructure.vault.task_parser import VaultTaskRepository
        from genome_toolkit.triage.infrastructure.vault.findings_parser import VaultFindingsRepository
        from genome_toolkit.triage.infrastructure.scripts.lab_adapter import VaultLabSignalRepository
        from genome_toolkit.triage.infrastructure.persistence.session_store import MarkdownSessionRepository
        from genome_toolkit.triage.application.triage_use_case import RunTriageSession
        from genome_toolkit.triage.presentation.tui.data_bridge import scored_item_to_stub, suggestion_to_stub

        task_repo = VaultTaskRepository(self._vault_path)
        findings_repo = VaultFindingsRepository(self._vault_path)
        lab_repo = VaultLabSignalRepository(self._vault_path)
        session_repo = MarkdownSessionRepository(self._vault_path)

        use_case = RunTriageSession(
            task_repo=task_repo,
            findings_repo=findings_repo,
            lab_signal_repo=lab_repo,
            session_repo=session_repo,
        )
        self._report = use_case.execute()
        self._items = [scored_item_to_stub(si) for si in self._report.scored_items]
        self._suggestions = [suggestion_to_stub(s) for s in self._report.suggestions]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Urgency", id="urgency"):
                yield UrgencyScreen(items=self._items)
            with TabPane("Context", id="context"):
                yield ContextScreen(items=self._items)
            with TabPane("Suggestions", id="suggestions"):
                yield SuggestionsScreen(suggestions=self._suggestions)
            with TabPane("History", id="history"):
                yield HistoryScreen(vault_path=self._vault_path)
        yield BatchBar()
        yield Footer()

    # ... rest of event handlers unchanged ...
```

- [ ] **Step 2: Update CLI to pass vault_path to TriageApp**

In `cli.py`, change the interactive section:
```python
    if interactive:
        from genome_toolkit.triage.presentation.tui.app import TriageApp
        app = TriageApp(vault_path=vault)
        app.run()
        return
```

- [ ] **Step 3: Run to verify no crash**

Run: `cd /path/to/genome-toolkit && PYTHONPATH=. python -m genome_toolkit.triage --vault ~/genome-vault --interactive`
Expected: TUI opens with real vault data

- [ ] **Step 4: Commit**

```bash
git add genome_toolkit/triage/presentation/tui/app.py genome_toolkit/triage/presentation/cli.py
git commit -m "feat(triage): wire TUI to real vault data via application layer"
```

---

### Task 3: Update all screens to accept data as constructor args

**Files:**
- Modify: `genome_toolkit/triage/presentation/tui/screens/urgency.py`
- Modify: `genome_toolkit/triage/presentation/tui/screens/context.py`
- Modify: `genome_toolkit/triage/presentation/tui/screens/suggestions.py`
- Modify: `genome_toolkit/triage/presentation/tui/screens/history.py`

- [ ] **Step 1: Update UrgencyScreen**

```python
# urgency.py — full replacement
"""Urgency screen: all items sorted by score descending."""
from __future__ import annotations

from textual.widget import Widget
from textual.app import ComposeResult
from textual.containers import VerticalScroll

from genome_toolkit.triage.presentation.tui.stub_data import ScoredItemStub, make_sample_items
from genome_toolkit.triage.presentation.tui.widgets.item_card import ItemCard


class UrgencyScreen(Widget):
    """Shows all items sorted by composite score, highest first."""

    DEFAULT_CSS = """
    UrgencyScreen {
        width: 1fr;
        height: 1fr;
    }
    """

    def __init__(self, items: list[ScoredItemStub] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._items = items if items is not None else make_sample_items()

    def compose(self) -> ComposeResult:
        sorted_items = sorted(self._items, key=lambda i: i.score, reverse=True)
        with VerticalScroll():
            for item in sorted_items:
                yield ItemCard(item)
```

- [ ] **Step 2: Update ContextScreen** (same pattern — accept `items` kwarg, fallback to stubs)

- [ ] **Step 3: Update SuggestionsScreen** — accept `suggestions` kwarg. On Approve button:
- Change button label to "Approved" with `variant="default"`
- Add strikethrough to title
- Post `SuggestionCard.Approved` message which app handles

```python
# In SuggestionCard:
    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.button.label = "Approved"
        event.button.variant = "default"
        event.button.disabled = True
        # Update title to strikethrough
        title_static = self.query_one(".suggestion-text", Static)
        title_static.update(Text(self.item.text, style="dim strike"))
        self.post_message(self.Approved(self.item))
```

- [ ] **Step 4: Update HistoryScreen** — accept `vault_path`, read real sessions:

```python
class HistoryScreen(Widget):
    def __init__(self, vault_path: Path | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._vault_path = vault_path

    def compose(self) -> ComposeResult:
        if self._vault_path:
            from genome_toolkit.triage.infrastructure.persistence.session_store import MarkdownSessionRepository
            repo = MarkdownSessionRepository(self._vault_path)
            sessions = repo.get_recent(limit=10)
            # Convert domain sessions to display format
            ...
        else:
            sessions = make_sample_history()
        ...
```

- [ ] **Step 5: Run TUI with real data to verify all tabs work**

- [ ] **Step 6: Commit**

```bash
git add genome_toolkit/triage/presentation/tui/screens/
git commit -m "feat(triage): all TUI screens accept real data, fallback to stubs"
```

---

### Task 4: Wire actions to ApplyDecisions — buttons that write to vault

**Files:**
- Modify: `genome_toolkit/triage/presentation/tui/app.py`
- Modify: `genome_toolkit/triage/presentation/tui/widgets/item_card.py`

- [ ] **Step 1: Add action collection to app**

In `TriageApp`, collect actions as `(TriageItem, Command)` tuples. Map from `ScoredItemStub` back to domain `ScoredItem` using item_id lookup.

```python
# In TriageApp:
    def _find_domain_item(self, stub: ScoredItemStub) -> TriageItem | None:
        """Find the domain item matching a stub."""
        if not self._report:
            return None
        for si in self._report.scored_items:
            if si.item.text == stub.text:
                return si.item
        return None

    def on_item_card_action_performed(self, event: ItemCard.ActionPerformed) -> None:
        domain_item = self._find_domain_item(event.card.item)
        if not domain_item:
            self.notify("Item not found in vault", severity="error")
            return

        command = None
        if event.action == "approve":
            from genome_toolkit.triage.domain.commands import ApproveCommand
            command = ApproveCommand(item_id=domain_item.item_id)
        elif event.action == "defer":
            from genome_toolkit.triage.domain.commands import DeferCommand
            command = DeferCommand(item_id=domain_item.item_id, days=7)
        elif event.action == "drop":
            from genome_toolkit.triage.domain.commands import DropCommand
            command = DropCommand(item_id=domain_item.item_id, note="triaged out via TUI")
        elif event.action == "priority_change":
            from genome_toolkit.triage.domain.commands import ChangePriorityCommand
            from genome_toolkit.triage.domain.item import Priority
            new_p = Priority[event.card.item.priority.upper()]
            command = ChangePriorityCommand(item_id=domain_item.item_id, new_priority=new_p)

        if command:
            self._pending_actions.append((domain_item, command))
            batch_bar = self.query_one(BatchBar)
            batch_bar.increment()
            self.notify(f"{event.action}: {domain_item.text[:40]}")
```

- [ ] **Step 2: Wire Apply button to ApplyDecisions**

```python
    def on_batch_bar_apply_requested(self, event: BatchBar.ApplyRequested) -> None:
        if not self._vault_path or not self._pending_actions:
            self.notify("Nothing to apply", severity="warning")
            return

        from genome_toolkit.triage.infrastructure.vault.task_parser import VaultTaskRepository
        from genome_toolkit.triage.infrastructure.persistence.session_store import MarkdownSessionRepository
        from genome_toolkit.triage.application.apply_decisions import ApplyDecisions

        task_repo = VaultTaskRepository(self._vault_path)
        session_repo = MarkdownSessionRepository(self._vault_path)
        applier = ApplyDecisions(task_repo=task_repo, session_repo=session_repo)

        try:
            session = applier.execute(self._pending_actions)
            self.notify(
                f"Applied {len(session.decisions)} changes to vault",
                severity="information",
            )
            self._pending_actions.clear()
            self.query_one(BatchBar).reset()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
```

- [ ] **Step 3: Add visual feedback to ItemCard on action**

```python
# In ItemCard:
    def key_a(self) -> None:
        """Approve/confirm item."""
        self.styles.opacity = 0.5
        self.query_one(".card-title", Static).update(
            Text(self.item.text, style="dim strike")
        )
        self.post_message(self.ActionPerformed(self, "approve"))

    def key_d(self) -> None:
        """Defer item."""
        self.query_one(".card-meta", Static).update(
            Text("DEFERRED +7 days", style="yellow bold")
        )
        self.post_message(self.ActionPerformed(self, "defer"))

    def key_x(self) -> None:
        """Drop item."""
        self.styles.opacity = 0.3
        self.query_one(".card-title", Static).update(
            Text(f"DROPPED: {self.item.text}", style="dim strike red")
        )
        self.post_message(self.ActionPerformed(self, "drop"))
```

- [ ] **Step 4: Test interactively**

Run: `cd /path/to/genome-toolkit && PYTHONPATH=. python -m genome_toolkit.triage --vault ~/genome-vault --interactive`
Test: Focus a card, press `a` → card dims + strikethrough. Press `q` → batch bar shows 1 pending. Click Apply → writes to vault.

- [ ] **Step 5: Commit**

```bash
git add genome_toolkit/triage/presentation/tui/
git commit -m "feat(triage): wire TUI actions to vault writes via ApplyDecisions"
```

---

### Task 5: Suggestion Approve creates real vault task

**Files:**
- Modify: `genome_toolkit/triage/presentation/tui/app.py`
- Modify: `genome_toolkit/triage/presentation/tui/screens/suggestions.py`

- [ ] **Step 1: Handle SuggestionCard.Approved in app**

```python
    def on_suggestion_card_approved(self, event) -> None:
        """Create a vault task from an approved suggestion."""
        stub = event.item
        if not self._vault_path or not self._report:
            return

        from genome_toolkit.triage.domain.commands import CreateCommand
        from genome_toolkit.triage.domain.item import Priority, Context

        # Find best file to add the task to
        target_file = self._vault_path / "Meta" / "Triage Report.md"

        command = CreateCommand(
            file_path=target_file,
            text=stub.text,
            priority=Priority[stub.priority.upper()],
            context=Context[stub.context.upper().replace("-", "_")],
        )

        # Find a dummy item for the decision record
        from genome_toolkit.triage.domain.item import TriageItem, ItemId, SourceLocation
        dummy = TriageItem(
            item_id=ItemId.from_content("triage", stub.text),
            source=SourceLocation(file_path=target_file, line_number=0),
            text=stub.text,
            priority=Priority[stub.priority.upper()],
            context=Context[stub.context.upper().replace("-", "_")],
        )
        self._pending_actions.append((dummy, command))
        self.query_one(BatchBar).increment()
        self.notify(f"Suggestion approved: {stub.text[:40]}")
```

- [ ] **Step 2: Commit**

```bash
git add genome_toolkit/triage/presentation/tui/
git commit -m "feat(triage): approve suggestion creates real vault task"
```

---

### Task 6: Update tests for new constructors

**Files:**
- Modify: `tests/triage/presentation/test_tui.py`

- [ ] **Step 1: Update test fixtures to pass items to screens**

Tests that create `TriageApp()` without args should still work (falls back to stubs). Add a test that creates `TriageApp(vault_path=fixture_vault)` and verifies real data loads.

- [ ] **Step 2: Run all tests**

Run: `cd /path/to/genome-toolkit && python -m pytest tests/triage/ -v --tb=short`
Expected: All pass

- [ ] **Step 3: Commit**

```bash
git add tests/
git commit -m "test(triage): update TUI tests for real data constructors"
```

---

### Task 7: Final integration test on real vault

- [ ] **Step 1: Run full CLI pipeline**

```bash
cd /path/to/genome-toolkit
PYTHONPATH=. python -m genome_toolkit.triage --vault ~/genome-vault
PYTHONPATH=. python -m genome_toolkit.triage --vault ~/genome-vault --svg /tmp/final-overview.svg
PYTHONPATH=. python -m genome_toolkit.triage --vault ~/genome-vault --svg-visit /tmp/final-visit.svg
PYTHONPATH=. python -m genome_toolkit.triage --vault ~/genome-vault --save
PYTHONPATH=. python -m genome_toolkit.triage --vault ~/genome-vault --interactive
```

- [ ] **Step 2: In TUI, test full workflow**

1. Navigate to Urgency tab, focus first card, press `a` → visual feedback
2. Navigate to Suggestions tab, click Approve → button changes
3. Press `q`, confirm Apply → changes written to vault
4. Re-launch TUI → History tab shows the session

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat(triage): complete TUI-to-vault integration — all actions functional"
```
