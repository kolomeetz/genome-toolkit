# Database Schema

Last updated: 2026-04-05

The toolkit uses two SQLite databases. This document is the source of truth for schema — update it whenever the structure changes.

---

## genome.db

Stores genetic variant data. Path configured via `GENOME_DB_PATH` env var (default: `./data/genome.db`).

### snps

Primary variant storage. One row per rsID.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| rsid | TEXT | PRIMARY KEY | dbSNP identifier (e.g., rs1801133) |
| chromosome | TEXT | NOT NULL | Chromosome: 1-22, X, Y, MT |
| position | INTEGER | NOT NULL | Genomic position (GRCh37/hg19) |
| genotype | TEXT | NOT NULL | Diploid genotype (e.g., T/T, A/G) |
| is_rsid | BOOLEAN | NOT NULL DEFAULT 1 | True if valid rsID format |
| source | TEXT | DEFAULT 'genotyped' | Data origin: `genotyped` (chip) or `imputed` |
| r2_quality | REAL | | Imputation quality score (0.0-1.0). NULL for genotyped. |
| imported_at | TEXT | DEFAULT datetime('now') | ISO timestamp of import |

**Indexes:**
- `idx_snps_chr_pos` on (chromosome, position)

**Notes:**
- Genotyped variants come from 23andMe/Ancestry/MyHeritage raw files
- Imputed variants come from Michigan/TOPMed imputation servers
- r2_quality thresholds: high (>0.9), good (>0.8), moderate (>0.5), low (>0.3) — see `config/default.yaml`

---

## users.db

Stores chat sessions and import history. Path: `$GENOME_DATA_DIR/users.db`.

### sessions

Chat session tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID session identifier |
| created_at | TEXT | NOT NULL | ISO timestamp |
| last_active | TEXT | NOT NULL | Last interaction timestamp |
| agent_session_id | TEXT | | Claude Agent SDK session ID |

### chat_messages

Conversation history per session.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Message ID |
| session_id | TEXT | NOT NULL, FK → sessions.id | Parent session |
| role | TEXT | NOT NULL | `user` or `assistant` |
| content | TEXT | NOT NULL | Message text (markdown) |
| timestamp | TEXT | NOT NULL | ISO timestamp |

### imports

Genome file import tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Import ID |
| session_id | TEXT | NOT NULL, FK → sessions.id | Session that triggered import |
| file_path | TEXT | NOT NULL | Path to source file |
| provider | TEXT | NOT NULL | `23andme`, `ancestry`, `myheritage`, `vcf` |
| variant_count | INTEGER | | Number of variants imported |
| imported_at | TEXT | | ISO timestamp of completion |
| status | TEXT | NOT NULL DEFAULT 'pending' | `pending`, `running`, `done`, `failed` |

---

## Future tables (planned)

These tables will be added as features are implemented:

### mental_health_actions (planned)

Track user progress on action card checklists.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Action ID |
| gene_symbol | TEXT | Associated gene |
| action_type | TEXT | consider / monitor / discuss / try |
| done | BOOLEAN | User marked as complete |
| done_at | TEXT | When completed |
| notes | TEXT | User notes |

### biomarkers (planned)

Lab results imported from blood work.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto ID |
| name | TEXT | Biomarker name (e.g., homocysteine) |
| value | REAL | Measured value |
| unit | TEXT | Unit of measurement |
| reference_low | REAL | Normal range low |
| reference_high | REAL | Normal range high |
| tested_at | TEXT | Date of test |
| source | TEXT | Lab name |
