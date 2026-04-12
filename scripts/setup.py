#!/usr/bin/env python3
"""Interactive setup wizard for Genome Toolkit.

Collects API keys, paths, TTS/STT preferences, and genetic parameters.
API keys are stored securely in macOS Keychain (fallback: .env file).
Other settings go to config/settings.yaml.

Usage:
    python scripts/setup.py                          # interactive wizard
    python scripts/setup.py --reconfigure            # re-run, keeping defaults
    python scripts/setup.py --auto                   # non-interactive, uses env vars + defaults
    python scripts/setup.py --auto --vault ~/vault --tts-voice leo --hide-views addiction
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from lib.secrets import get_secret, set_secret, SECRETS

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
SETTINGS_PATH = CONFIG_DIR / "settings.yaml"
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_existing() -> dict:
    if SETTINGS_PATH.is_file():
        with open(SETTINGS_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def ask(prompt: str, default: str = "", secret: bool = False, options: list[str] | None = None) -> str:
    """Prompt user for input with optional default and validation."""
    suffix = ""
    if options:
        suffix = f" [{'/'.join(options)}]"
    if default and not secret:
        suffix += f" (default: {default})"
    elif default and secret:
        suffix += " (already set, Enter to keep)"

    full_prompt = f"  {prompt}{suffix}: "

    if secret:
        try:
            import getpass
            val = getpass.getpass(full_prompt)
        except (ImportError, EOFError):
            val = input(full_prompt)
    else:
        val = input(full_prompt)

    val = val.strip()
    if not val:
        return default

    if options and val not in options:
        print(f"    Invalid choice. Options: {', '.join(options)}")
        return ask(prompt, default, secret, options)

    return val


def ask_list(prompt: str, existing: list[str] | None = None) -> list[str]:
    """Prompt for a comma-separated list."""
    default_str = ", ".join(existing) if existing else ""
    suffix = f" (default: {default_str})" if default_str else ""
    val = input(f"  {prompt} (comma-separated){suffix}: ").strip()
    if not val:
        return existing or []
    return [item.strip() for item in val.split(",") if item.strip()]


def section(title: str):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return key
    return key[:4] + "..." + key[-4:]


def run_setup():
    existing = load_existing()

    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║         GENOME TOOLKIT — SETUP WIZARD           ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    print("  Configure your toolkit step by step.")
    print("  Press Enter to accept defaults shown in parentheses.")

    # --- API Keys ---
    section("API KEYS")
    print("  Keys are stored in macOS Keychain (or .env as fallback).")
    print()

    current_anthropic = get_secret("anthropic_api_key")
    if current_anthropic:
        print(f"  Current Anthropic key: {mask_key(current_anthropic)}")
    anthropic_key = ask("Anthropic API key", default=current_anthropic, secret=True)

    current_groq = get_secret("groq_api_key")
    if current_groq:
        print(f"  Current Groq key: {mask_key(current_groq)}")
    groq_key = ask("Groq API key (for Orpheus TTS)", default=current_groq, secret=True)

    current_elevenlabs = get_secret("elevenlabs_api_key")
    if current_elevenlabs:
        print(f"  Current ElevenLabs key: {mask_key(current_elevenlabs)}")
    elevenlabs_key = ask("ElevenLabs API key (optional)", default=current_elevenlabs, secret=True)

    current_deepgram = get_secret("deepgram_api_key")
    if current_deepgram:
        print(f"  Current Deepgram key: {mask_key(current_deepgram)}")
    deepgram_key = ask("Deepgram API key (optional)", default=current_deepgram, secret=True)

    # --- Paths ---
    section("PATHS")

    db_path = ask(
        "Genome database path",
        default=existing.get("genome_db_path", "./data/genome.db"),
    )
    vault_path = ask(
        "Obsidian vault path",
        default=existing.get("genome_vault_path", "~/genome-vault"),
    )
    # Validate vault path
    expanded_vault = Path(vault_path).expanduser()
    if not expanded_vault.exists():
        print(f"    Warning: {expanded_vault} does not exist yet.")
        create = ask("Create it?", default="n", options=["y", "n"])
        if create == "y":
            expanded_vault.mkdir(parents=True, exist_ok=True)
            print(f"    Created {expanded_vault}")

    # --- TTS ---
    section("TEXT-TO-SPEECH")

    tts_existing = existing.get("tts", {})
    tts_provider = ask(
        "TTS provider",
        default=tts_existing.get("provider", "orpheus"),
        options=["orpheus", "elevenlabs", "deepgram", "browser", "none"],
    )

    tts_voice = tts_existing.get("voice", "tara")
    tts_emotion = tts_existing.get("emotion_default", "")
    tts_speed = tts_existing.get("speed", 1.0)

    if tts_provider == "orpheus":
        if not groq_key:
            print("    Note: Orpheus requires a Groq API key. Set it above or via GROQ_API_KEY env var.")
        tts_voice = ask(
            "Voice",
            default=tts_voice,
            options=["tara", "leah", "mia", "jess", "leo", "dan"],
        )
        tts_emotion = ask(
            "Default emotion (blank for neutral)",
            default=tts_emotion,
        )
        speed_str = ask("Playback speed", default=str(tts_speed))
        try:
            tts_speed = float(speed_str)
        except ValueError:
            tts_speed = 1.0
    elif tts_provider == "elevenlabs":
        if not elevenlabs_key:
            print("    Note: ElevenLabs requires an API key. Set it above or via ELEVENLABS_API_KEY env var.")
        tts_voice = ask(
            "Voice ID (see /api/tts/voices for list)",
            default=tts_voice if tts_voice else "21m00Tcm4TlvDq8ikWAM",
        )
    elif tts_provider == "deepgram":
        if not deepgram_key:
            print("    Note: Deepgram requires an API key. Set it above or via DEEPGRAM_API_KEY env var.")
        tts_voice = ask(
            "Voice model",
            default=tts_voice if tts_voice else "aura-asteria-en",
        )

    # --- STT ---
    section("SPEECH-TO-TEXT")

    stt_existing = existing.get("stt", {})
    stt_lang = ask(
        "STT language (BCP-47)",
        default=stt_existing.get("language", "en-US"),
    )

    # --- Genetics ---
    section("GENETICS PROFILE")

    gen_existing = existing.get("genetics", {})
    population = ask(
        "Ancestry population for PRS",
        default=gen_existing.get("population", "EUR"),
        options=["EUR", "AFR", "EAS", "SAS", "AMR", "NFE", "FIN"],
    )

    print("\n  Current medications help prioritize pharmacogenomics analysis.")
    medications = ask_list(
        "Current medications",
        existing=gen_existing.get("medications", []),
    )

    print("\n  Health goals determine which genes are prioritized during onboarding.")
    print("  Options: medication_safety, mental_health, longevity, nutrition, fitness, comprehensive")
    health_goals = ask_list(
        "Health goals",
        existing=gen_existing.get("health_goals", []),
    )

    # --- Display ---
    section("DISPLAY")

    ALL_VIEWS = ["snps", "mental-health", "pgx", "addiction", "risk"]
    VIEW_LABELS = {
        "snps": "SNP Browser",
        "mental-health": "Mental Health",
        "pgx": "PGx / Drugs",
        "addiction": "Addiction",
        "risk": "Risk Landscape",
    }

    display_existing = existing.get("display", {})
    existing_views = display_existing.get("views", ALL_VIEWS)

    print("  Choose which sections to show in the navigation bar.")
    print("  SNP Browser is always shown. Toggle others with y/n.\n")

    enabled_views = ["snps"]
    for v in ALL_VIEWS:
        if v == "snps":
            continue
        is_on = v in existing_views
        choice = ask(
            f"Show {VIEW_LABELS[v]}?",
            default="y" if is_on else "n",
            options=["y", "n"],
        )
        if choice == "y":
            enabled_views.append(v)

    display_theme = display_existing.get("theme", "warm")
    display_units = display_existing.get("units", "metric")

    # --- Store API keys securely ---
    section("STORING API KEYS")
    for key_name, key_value in [("anthropic_api_key", anthropic_key), ("groq_api_key", groq_key), ("elevenlabs_api_key", elevenlabs_key), ("deepgram_api_key", deepgram_key)]:
        if key_value:
            method = set_secret(key_name, key_value)
            env_name = SECRETS.get(key_name, key_name.upper())
            print(f"  {env_name}: stored in {method}")
        else:
            print(f"  {SECRETS.get(key_name, key_name.upper())}: skipped (empty)")

    # --- Build settings dict (no secrets!) ---
    settings = {
        "genome_db_path": db_path,
        "genome_vault_path": vault_path,
        "tts": {
            "provider": tts_provider,
            "voice": tts_voice,
            "emotion_default": tts_emotion,
            "speed": tts_speed,
        },
        "stt": {
            "language": stt_lang,
        },
        "genetics": {
            "population": population,
            "medications": medications,
            "health_goals": health_goals,
        },
        "display": {
            "theme": display_theme,
            "units": display_units,
            "views": enabled_views,
        },
    }

    # --- Write settings.yaml ---
    section("SAVING CONFIGURATION")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    header = (
        "# User Settings — generated by scripts/setup.py\n"
        "# Re-run `python scripts/setup.py` to reconfigure\n\n"
    )
    with open(SETTINGS_PATH, "w") as f:
        f.write(header)
        yaml.dump(settings, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"  Saved: {SETTINGS_PATH}")

    # --- Write .env (paths only — API keys are in keychain) ---
    env_lines = [
        "# Generated by scripts/setup.py",
        "# API keys are stored in macOS Keychain (service: genome-toolkit)",
        "",
        f"GENOME_DB_PATH={db_path}",
        f"GENOME_DATA_DIR=./data",
        f"GENOME_VAULT_PATH={vault_path}",
        "",
    ]

    with open(ENV_PATH, "w") as f:
        f.write("\n".join(env_lines))

    print(f"  Saved: {ENV_PATH}")

    # --- Summary ---
    section("SETUP COMPLETE")
    print(f"  TTS:         {tts_provider}" + (f" ({tts_voice})" if tts_provider != "browser" else ""))
    print(f"  STT:         {stt_lang}")
    print(f"  Views:       {', '.join(enabled_views)}")
    hidden = [v for v in ALL_VIEWS if v not in enabled_views]
    if hidden:
        print(f"  Hidden:      {', '.join(hidden)}")
    print(f"  Population:  {population}")
    if medications:
        print(f"  Medications: {', '.join(medications)}")
    if health_goals:
        print(f"  Goals:       {', '.join(health_goals)}")
    print(f"  Vault:       {vault_path}")
    print()
    print("  Next steps:")
    print("    1. Import your genome data:  python scripts/genome_init.py --help")
    print("    2. Start the app:            ./start.sh")
    print("    3. Re-configure anytime:     python scripts/setup.py")
    print()


ALL_VIEWS_DEFAULT = ["snps", "mental-health", "pgx", "addiction", "risk"]


def run_auto_setup(args):
    """Non-interactive setup. Reads from CLI args and env vars, writes config files."""
    existing = load_existing()

    # --- Resolve values: CLI arg > env var > existing config > default ---
    vault_path = args.vault or os.environ.get("GENOME_VAULT_PATH") or existing.get("genome_vault_path", "~/genome-vault")
    db_path = args.db or os.environ.get("GENOME_DB_PATH") or existing.get("genome_db_path", "./data/genome.db")

    tts_existing = existing.get("tts", {})
    tts_provider = args.tts_provider or os.environ.get("TTS_PROVIDER") or tts_existing.get("provider", "orpheus")
    tts_voice = args.tts_voice or tts_existing.get("voice", "tara")
    tts_emotion = tts_existing.get("emotion_default", "")
    tts_speed = tts_existing.get("speed", 1.0)

    stt_lang = args.stt_lang or existing.get("stt", {}).get("language", "en-US")

    gen_existing = existing.get("genetics", {})
    population = args.population or gen_existing.get("population", "EUR")
    medications = gen_existing.get("medications", [])
    health_goals = gen_existing.get("health_goals", [])

    display_existing = existing.get("display", {})
    display_theme = display_existing.get("theme", "warm")
    display_units = display_existing.get("units", "metric")

    # Views: start with all, remove hidden ones
    enabled_views = list(display_existing.get("views", ALL_VIEWS_DEFAULT))
    if args.hide_views:
        for v in args.hide_views:
            if v in enabled_views and v != "snps":
                enabled_views.remove(v)
    if args.show_views:
        for v in args.show_views:
            if v not in enabled_views and v in ALL_VIEWS_DEFAULT:
                enabled_views.append(v)
    if "snps" not in enabled_views:
        enabled_views.insert(0, "snps")

    # --- Store API keys ---
    keys = {
        "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
        "groq_api_key": os.environ.get("GROQ_API_KEY", ""),
        "elevenlabs_api_key": os.environ.get("ELEVENLABS_API_KEY", ""),
        "deepgram_api_key": os.environ.get("DEEPGRAM_API_KEY", ""),
    }
    for key_name, key_value in keys.items():
        if key_value:
            method = set_secret(key_name, key_value)
            print(f"  {SECRETS.get(key_name, key_name.upper())}: stored in {method}")

    # --- Build and write settings ---
    settings = {
        "genome_db_path": db_path,
        "genome_vault_path": vault_path,
        "tts": {
            "provider": tts_provider,
            "voice": tts_voice,
            "emotion_default": tts_emotion,
            "speed": tts_speed,
        },
        "stt": {"language": stt_lang},
        "genetics": {
            "population": population,
            "medications": medications,
            "health_goals": health_goals,
        },
        "display": {
            "theme": display_theme,
            "units": display_units,
            "views": enabled_views,
        },
    }

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    header = "# User Settings — generated by scripts/setup.py --auto\n\n"
    with open(SETTINGS_PATH, "w") as f:
        f.write(header)
        yaml.dump(settings, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    env_lines = [
        "# Generated by scripts/setup.py --auto",
        f"GENOME_DB_PATH={db_path}",
        f"GENOME_DATA_DIR=./data",
        f"GENOME_VAULT_PATH={vault_path}",
        "",
    ]
    with open(ENV_PATH, "w") as f:
        f.write("\n".join(env_lines))

    print(f"  Config: {SETTINGS_PATH}")
    print(f"  Env:    {ENV_PATH}")
    print(f"  TTS:    {tts_provider} ({tts_voice})")
    print(f"  Views:  {', '.join(enabled_views)}")
    print(f"  Vault:  {vault_path}")
    print("  Done.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Genome Toolkit setup")
    parser.add_argument("--auto", action="store_true", help="Non-interactive setup (agent-friendly)")
    parser.add_argument("--vault", help="Obsidian vault path")
    parser.add_argument("--db", help="Genome database path")
    parser.add_argument("--tts-provider", help="TTS provider: orpheus|elevenlabs|deepgram|browser|none")
    parser.add_argument("--tts-voice", help="TTS voice ID (e.g. leo, tara)")
    parser.add_argument("--stt-lang", help="STT language (BCP-47, e.g. en-US)")
    parser.add_argument("--population", help="Ancestry population: EUR|AFR|EAS|SAS|AMR|NFE|FIN")
    parser.add_argument("--hide-views", nargs="+", help="Views to hide (e.g. addiction risk)")
    parser.add_argument("--show-views", nargs="+", help="Views to show (e.g. addiction)")
    parser.add_argument("--reconfigure", action="store_true", help="Re-run keeping existing defaults")

    args = parser.parse_args()

    if args.auto:
        run_auto_setup(args)
    else:
        try:
            run_setup()
        except KeyboardInterrupt:
            print("\n\n  Setup cancelled.")
            sys.exit(1)
