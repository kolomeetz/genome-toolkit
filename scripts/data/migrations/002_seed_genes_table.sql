-- 002: This migration is a no-op placeholder. Gene seeding is done by
-- scripts/seed_genes.py which reads gene_rsid_map.json and inserts/updates
-- the genes table. This allows the map to be updated without new migrations.
--
-- Run: python3 scripts/seed_genes.py [--db path/to/genome.db]
SELECT 1;
