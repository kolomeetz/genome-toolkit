-- 006: Normalize genes.rsids from plain TEXT to JSON arrays
--
-- Converts any existing comma-separated or plain-text rsids values to JSON arrays
-- so that json_each(genes.rsids) can be used in queries.
--
-- Handles:
--   NULL             -> left as NULL
--   ''               -> left as NULL
--   '[]'             -> left as-is (already valid JSON array)
--   '["rs123"]'      -> left as-is (already valid JSON array)
--   'rs123'          -> '["rs123"]'
--   'rs123,rs456'    -> '["rs123","rs456"]'
--   ' rs123, rs456 ' -> '["rs123","rs456"]' (whitespace trimmed)

UPDATE genes
SET rsids = (
    WITH trimmed AS (
        SELECT TRIM(rsids) AS v
    )
    SELECT
        CASE
            -- Already a JSON array: starts with '[' and ends with ']'
            WHEN (SELECT v FROM trimmed) LIKE '[%]' THEN rsids
            -- Single rsid (no comma): wrap in JSON array
            WHEN instr((SELECT v FROM trimmed), ',') = 0
                THEN json_array(TRIM(rsids))
            -- Comma-separated list: split and rebuild as JSON array
            ELSE (
                WITH RECURSIVE
                parts(rest, item) AS (
                    -- seed: full trimmed string with sentinel comma appended
                    SELECT TRIM(rsids) || ',', NULL
                    UNION ALL
                    SELECT
                        SUBSTR(rest, instr(rest, ',') + 1),
                        TRIM(SUBSTR(rest, 1, instr(rest, ',') - 1))
                    FROM parts
                    WHERE instr(rest, ',') > 0
                      AND TRIM(SUBSTR(rest, 1, instr(rest, ',') - 1)) != ''
                )
                SELECT json_group_array(item)
                FROM parts
                WHERE item IS NOT NULL
            )
        END
)
WHERE rsids IS NOT NULL
  AND TRIM(rsids) != ''
  AND TRIM(rsids) != '[]';
