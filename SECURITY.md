# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in Genome Toolkit, please report it privately:

- **Email**: Contact [@glebis](https://github.com/glebis) via GitHub (open a private security advisory on this repository, or DM on GitHub)
- **Expected response time**: Within 72 hours for initial acknowledgment, fix within 14 days for critical issues
- **Responsible disclosure**: Please allow reasonable time for a fix before public disclosure. We will credit reporters in the changelog unless they prefer anonymity.

Do **not** open a public issue for security vulnerabilities.

## Data Handling Guarantees

Genome Toolkit is designed for local-first, privacy-preserving personal genomics:

- **Raw genome data never leaves your machine** unless you explicitly upload to an imputation server (Michigan/TOPMed)
- **SQLite database (`genome.db`) is gitignored** and never committed to version control
- **No telemetry, analytics, or tracking** of any kind
- **API keys** are stored in macOS Keychain by default; optionally in SOPS-encrypted files for team use
- **Reports reference rsIDs**, not bulk genotype dumps
- The web UI runs on `localhost` only — there is no hosted/cloud version

## Scope Boundary

Genome Toolkit is **not a medical device**. It is not HIPAA-compliant, not FDA-cleared, and not intended for clinical diagnosis or treatment decisions. It is a personal research and education tool.

Genetic information should always be interpreted by qualified healthcare professionals. The evidence tier system (E1-E5) reflects published research, not clinical recommendations.

## What We Consider Security Issues

- Exposure of raw genome data (e.g., via accidental git commit, insecure file permissions, or API response leaking genotypes)
- API key leaks (Anthropic, Groq, ElevenLabs, etc.) through logs, error messages, or frontend exposure
- Insecure defaults (e.g., binding to `0.0.0.0` instead of `localhost`, permissive CORS)
- XSS, injection, or path traversal in the web UI or API endpoints
- SOPS/age misconfiguration that could expose encrypted secrets
- Dependency vulnerabilities that create a realistic attack path

## What Is NOT a Security Issue

- Genetic interpretation accuracy (e.g., "this gene note overstates the effect of rs1234")
- Evidence tier disagreements (e.g., "this should be E3 not E2")
- Imputation quality or statistical methodology
- UI bugs that do not expose sensitive data

These are legitimate feedback — please open a regular GitHub issue for them.

## Dependencies

- We monitor dependencies via GitHub Dependabot alerts
- Critical/high severity vulnerabilities in direct dependencies are patched promptly
- We pin major versions and review dependency updates before merging
- If you notice a vulnerable dependency, please open an issue (or a security advisory if it creates an exploitable path)
