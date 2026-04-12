# Contributing to Genome Toolkit

## Prerequisites

- Python 3.10+
- Node.js 22+
- SQLite 3
- Git

## Dev Setup

```bash
# Clone
git clone https://github.com/glebis/genome-toolkit.git
cd genome-toolkit

# Backend
pip install -e ".[dev,web]"

# Frontend
cd frontend && npm install && cd ..

# Non-interactive setup (reads API keys from env vars or macOS Keychain)
python scripts/setup.py --auto

# Start backend
uvicorn backend.app.main:app --port 8000

# Start frontend (separate terminal)
cd frontend && npm run dev
```

Open http://localhost:5173.

## Project Structure

```
backend/         FastAPI backend (routes, agent, TTS, DB)
frontend/        React + TypeScript + Vite
config/          YAML/JSON configuration
scripts/         Python pipeline (import, setup, migrations)
skills/          Claude Code skill definitions
tests/           Python test suite (pytest)
vault-template/  Obsidian vault starter
```

See [AGENTS.md](AGENTS.md) for detailed architecture and conventions.

## Running Tests

```bash
# Backend
python -m pytest tests/ -v

# Frontend
cd frontend && npx vitest run

# Frontend with coverage
cd frontend && npx vitest run --coverage
```

Both backend and frontend tests must pass before submitting a PR.

## Code Style

- **Python**: No formatter enforced yet. Follow the existing style in the codebase.
- **TypeScript**: No CSS framework. Use inline styles. Font: IBM Plex Mono.
- Keep imports organized and remove unused ones.

## Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `chore:` maintenance, dependencies
- `refactor:` code restructuring without behavior change
- `test:` adding or updating tests
- `docs:` documentation only

Examples:
```
feat: add CYP2C19 metabolizer status to PGx view
fix: handle missing rsID in Genotek provider
test: add coverage for GWAS config loading
```

## Pull Request Process

1. Create a feature branch from `main`.
2. Describe what changed and why in the PR description.
3. Add tests for new functionality.
4. Ensure both backend (`pytest`) and frontend (`vitest`) tests pass.
5. No sensitive data in the diff (genome files, API keys, health info).

## Adding a Genome Provider

Provider parsers live in `scripts/lib/providers/`. Each provider module detects its file format and parses variants into a common schema.

See `scripts/lib/providers/genotek.py` as a reference implementation. Key steps:

1. Create `scripts/lib/providers/<name>.py` with a detection function and parser.
2. Register it in the provider registry.
3. Add format signature to `config/provider_formats.yaml`.
4. Add tests.

## Adding a TTS Provider

TTS providers live in `backend/app/tts/`. Each implements the `TTSProvider` base class.

1. Create `backend/app/tts/<name>.py` extending the base class.
2. Register in `backend/app/tts/registry.py`.
3. Add the provider option to `scripts/setup.py`.

## Privacy Rules

**NEVER commit any of the following:**

- Raw genome data files (`.txt`, `.csv`, `.vcf` containing genotypes)
- SQLite database files (`genome.db`, `users.db`)
- API keys or secrets (`.env`, `config/secrets.yaml` decrypted)
- Personal health information (lab results, assessment scores, vault notes)

These are all covered by `.gitignore`, but double-check your diffs before pushing.
