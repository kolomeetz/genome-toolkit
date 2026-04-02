#!/usr/bin/env python3
"""Daily health logger — fast CLI for supplement/symptom/intervention tracking.

Usage:
    daily_log.py                    # Interactive: toggle supplements, rate symptoms
    daily_log.py --quick            # Just supplements (boolean toggles)
    daily_log.py --show             # Show today's log
    daily_log.py --date 2026-04-01  # Log for a specific date
    daily_log.py --edit             # Open today's note in $EDITOR
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

def _resolve_vault() -> Path:
    """Resolve vault root from env, config, or CWD."""
    import os
    env = os.environ.get("GENOME_VAULT_ROOT")
    if env:
        return Path(env).expanduser()
    # Try loading from config
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from lib.config import VAULT_ROOT as cfg_root
        return Path(cfg_root)
    except ImportError:
        pass
    # Fallback: CWD or common location
    cwd = Path.cwd()
    if (cwd / "Dashboard.md").exists():
        return cwd
    home_vault = Path.home() / "Brains" / "genome"
    if home_vault.exists():
        return home_vault
    return cwd


VAULT_ROOT = _resolve_vault()
DAILY_DIR = VAULT_ROOT / "Daily"
TEMPLATE = VAULT_ROOT / "Templates" / "_Daily.md"


def load_template() -> str:
    if TEMPLATE.exists():
        return TEMPLATE.read_text(encoding="utf-8")
    return ""


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter manually (no PyYAML dependency)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    fm = {}
    current_section = None
    current_dict = None

    for line in parts[1].strip().split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # Top-level key
        if indent == 0 and ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "" or val == "null":
                current_section = key
                current_dict = {}
                fm[key] = current_dict
            elif val.startswith("'") or val.startswith('"'):
                fm[key] = val.strip("'\"")
                current_section = None
                current_dict = None
            elif val == "true":
                fm[key] = True
            elif val == "false":
                fm[key] = False
            else:
                fm[key] = val
                current_section = None
                current_dict = None
        elif indent > 0 and current_dict is not None and ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "true":
                current_dict[key] = True
            elif val == "false":
                current_dict[key] = False
            elif val == "null":
                current_dict[key] = None
            else:
                try:
                    current_dict[key] = int(val)
                except ValueError:
                    try:
                        current_dict[key] = float(val)
                    except ValueError:
                        current_dict[key] = val

    return fm, parts[2]


def serialize_frontmatter(fm: dict, body: str) -> str:
    """Serialize frontmatter dict back to YAML string."""
    lines = ["---"]
    for key, val in fm.items():
        if isinstance(val, dict):
            lines.append(f"{key}:")
            for k, v in val.items():
                if v is None:
                    lines.append(f"  {k}: null")
                elif isinstance(v, bool):
                    lines.append(f"  {k}: {'true' if v else 'false'}")
                elif isinstance(v, (int, float)):
                    lines.append(f"  {k}: {v}")
                else:
                    lines.append(f"  {k}: {v}")
        elif isinstance(val, bool):
            lines.append(f"{key}: {'true' if val else 'false'}")
        elif isinstance(val, list):
            lines.append(f"{key}:")
            for item in val:
                lines.append(f"  - {item}")
        else:
            if any(c in str(val) for c in ":#{}[]"):
                lines.append(f"{key}: '{val}'")
            else:
                lines.append(f"{key}: {val}")
    lines.append("---")
    return "\n".join(lines) + body


def get_daily_path(d: date) -> Path:
    return DAILY_DIR / f"{d.isoformat()}.md"


def create_daily_note(d: date) -> Path:
    """Create daily note from template."""
    path = get_daily_path(d)
    DAILY_DIR.mkdir(parents=True, exist_ok=True)

    if path.exists():
        return path

    template = load_template()
    content = template.replace("{{date:YYYY-MM-DD}}", d.isoformat())
    content = content.replace("{{date}}", d.isoformat())
    path.write_text(content, encoding="utf-8")
    return path


def interactive_log(d: date, quick: bool = False):
    """Interactive logging session."""
    path = create_daily_note(d)
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    print(f"\n  Daily Log — {d.isoformat()}")
    print(f"  {'=' * 30}\n")

    # Supplements
    supps = fm.get("supplements", {})
    if supps:
        print("  SUPPLEMENTS (y/n/Enter=yes):")
        for key in supps:
            current = supps[key]
            marker = "✓" if current else "·"
            resp = input(f"    {marker} {key}? ").strip().lower()
            if resp in ("n", "no", "0"):
                supps[key] = False
            else:
                supps[key] = True
        fm["supplements"] = supps
        print()

    # Medications
    meds = fm.get("medications", {})
    if meds:
        print("  MEDICATIONS (y/n/Enter=yes):")
        for key in meds:
            resp = input(f"    · {key}? ").strip().lower()
            if resp in ("n", "no", "0"):
                meds[key] = False
            else:
                meds[key] = True
        fm["medications"] = meds
        print()

    if not quick:
        # Symptoms
        symptoms = fm.get("symptoms", {})
        if symptoms:
            print("  SYMPTOMS (0-10, Enter=skip):")
            for key in symptoms:
                resp = input(f"    {key.replace('_', ' ')}: ").strip()
                if resp == "":
                    symptoms[key] = None
                else:
                    try:
                        val = int(resp)
                        symptoms[key] = max(0, min(10, val))
                    except ValueError:
                        symptoms[key] = None
            fm["symptoms"] = symptoms
            print()

        # Interventions
        interventions = fm.get("interventions", {})
        if interventions:
            print("  INTERVENTIONS (y/n/Enter=no):")
            for key in interventions:
                resp = input(f"    · {key.replace('_', ' ')}? ").strip().lower()
                if resp in ("y", "yes", "1"):
                    interventions[key] = True
                else:
                    interventions[key] = False
            fm["interventions"] = interventions
            print()

        # Metrics
        metrics = fm.get("metrics", {})
        if metrics:
            print("  METRICS (number, Enter=skip):")
            for key in metrics:
                unit = ""
                if "hours" in key:
                    unit = "h"
                elif "mg" in key:
                    unit = "mg"
                resp = input(f"    {key.replace('_', ' ')}{f' ({unit})' if unit else ''}: ").strip()
                if resp == "":
                    metrics[key] = None
                else:
                    try:
                        metrics[key] = float(resp) if "." in resp else int(resp)
                    except ValueError:
                        metrics[key] = None
            fm["metrics"] = metrics
            print()

    # Save
    new_text = serialize_frontmatter(fm, body)
    path.write_text(new_text, encoding="utf-8")

    # Summary
    supp_count = sum(1 for v in fm.get("supplements", {}).values() if v is True)
    supp_total = len(fm.get("supplements", {}))
    print(f"  Saved → {path.relative_to(VAULT_ROOT)}")
    print(f"  Supplements: {supp_count}/{supp_total}")

    symp_logged = sum(1 for v in fm.get("symptoms", {}).values() if v is not None)
    if symp_logged:
        print(f"  Symptoms logged: {symp_logged}")

    int_done = sum(1 for v in fm.get("interventions", {}).values() if v is True)
    if int_done:
        print(f"  Interventions: {int_done}")

    print()


def show_log(d: date):
    """Show today's log."""
    path = get_daily_path(d)
    if not path.exists():
        print(f"  No daily note for {d.isoformat()}")
        return

    text = path.read_text(encoding="utf-8")
    fm, _ = parse_frontmatter(text)

    print(f"\n  Daily Log — {d.isoformat()}")
    print(f"  {'=' * 30}\n")

    for category in ["medications", "supplements", "symptoms", "interventions", "metrics"]:
        data = fm.get(category, {})
        if not data:
            continue
        print(f"  {category.upper()}:")
        for key, val in data.items():
            if isinstance(val, bool):
                icon = "✓" if val else "✗"
                print(f"    {icon} {key}")
            elif val is None:
                print(f"    · {key}: —")
            else:
                print(f"    → {key}: {val}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Daily health logger")
    parser.add_argument("--date", "-d", default=None, help="Date (YYYY-MM-DD)")
    parser.add_argument("--quick", "-q", action="store_true", help="Supplements only")
    parser.add_argument("--show", "-s", action="store_true", help="Show today's log")
    parser.add_argument("--edit", "-e", action="store_true", help="Open in editor")
    args = parser.parse_args()

    d = date.fromisoformat(args.date) if args.date else date.today()

    if args.show:
        show_log(d)
    elif args.edit:
        import os
        path = create_daily_note(d)
        editor = os.environ.get("EDITOR", "vim")
        os.execlp(editor, editor, str(path))
    else:
        interactive_log(d, quick=args.quick)


if __name__ == "__main__":
    main()
