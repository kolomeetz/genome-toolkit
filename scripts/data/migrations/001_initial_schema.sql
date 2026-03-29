-- 001: Initial schema — profiles, variant_calls, enrichments, pipeline tracking

CREATE TABLE IF NOT EXISTS profiles (
    profile_id   TEXT PRIMARY KEY,
    display_name TEXT,
    provider     TEXT NOT NULL,
    provider_version TEXT,
    file_hash    TEXT,
    assembly     TEXT DEFAULT 'GRCh37',
    snp_count    INTEGER,
    created_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS imports (
    import_id       TEXT PRIMARY KEY,
    profile_id      TEXT NOT NULL REFERENCES profiles(profile_id),
    source_file     TEXT,
    file_hash       TEXT,
    detected_format TEXT,
    assembly        TEXT,
    qc_json         TEXT,
    started_at      TEXT DEFAULT (datetime('now')),
    finished_at     TEXT,
    status          TEXT DEFAULT 'running',
    stats           TEXT
);

CREATE TABLE IF NOT EXISTS snps (
    rsid         TEXT NOT NULL,
    profile_id   TEXT NOT NULL DEFAULT 'default',
    chromosome   TEXT NOT NULL,
    position     INTEGER NOT NULL,
    genotype     TEXT NOT NULL,
    is_rsid      BOOLEAN NOT NULL DEFAULT 1,
    source       TEXT NOT NULL DEFAULT 'genotyped',
    import_date  TEXT,
    r2_quality   REAL,
    import_id    TEXT,
    imported_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (rsid, profile_id)
);

CREATE INDEX IF NOT EXISTS idx_snps_chr_pos ON snps(chromosome, position);
CREATE INDEX IF NOT EXISTS idx_snps_profile ON snps(profile_id);
CREATE INDEX IF NOT EXISTS idx_snps_source ON snps(source);

CREATE TABLE IF NOT EXISTS enrichments (
    rsid       TEXT NOT NULL,
    source     TEXT NOT NULL,
    data       TEXT NOT NULL,
    fetched_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,
    PRIMARY KEY (rsid, source)
);

CREATE INDEX IF NOT EXISTS idx_enrichments_source ON enrichments(source);
CREATE INDEX IF NOT EXISTS idx_enrichments_expires ON enrichments(expires_at);

CREATE TABLE IF NOT EXISTS genes (
    gene_symbol TEXT PRIMARY KEY,
    full_name   TEXT,
    chromosome  TEXT,
    rsids       TEXT
);

CREATE TABLE IF NOT EXISTS phenotypes (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT UNIQUE NOT NULL,
    category TEXT,
    genes    TEXT,
    rsids    TEXT
);

CREATE TABLE IF NOT EXISTS notes (
    note_path     TEXT PRIMARY KEY,
    note_type     TEXT NOT NULL,
    generated_at  TEXT,
    data_version  TEXT,
    needs_refresh BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    script      TEXT NOT NULL,
    started_at  TEXT DEFAULT (datetime('now')),
    finished_at TEXT,
    status      TEXT,
    stats       TEXT
);

-- Legacy compatibility view: looks like the old single-profile snps table
CREATE VIEW IF NOT EXISTS snps_v1 AS
SELECT rsid, chromosome, position, genotype, is_rsid, imported_at
FROM snps
WHERE profile_id = 'default';
