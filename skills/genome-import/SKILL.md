---
name: genome-import
description: |
  Universal genome data import supporting 23andMe v4/v5, AncestryDNA, MyHeritage,
  Nebula, and generic VCF. Also handles imputation prep and post-imputation import.
  Triggers on: /genome-import, "import my DNA data", "add raw file",
  "prepare for imputation", "import imputed data".
---

# Genome Import

Import raw genome data from any supported DTC provider or VCF file.

## Vault Configuration
- Config: `$GENOME_VAULT_ROOT` or config/default.yaml
- Database: `data/genome.db`
- Raw data: `data/raw/` (user places their file here)
- Provider detection: `config/provider_formats.yaml`

## Sub-Workflows

### A: Raw Import (default)

1. **Auto-detect provider**: Run `python3 scripts/genome_init.py --detect-only <file>`
2. **Confirm with user**: Show detected provider, assembly, confidence
3. **Import**: Run `python3 scripts/genome_init.py <file> --profile <name>`
4. **Show QC report**: total SNPs, filtered, chromosome distribution
5. **Suggest next steps**: onboarding or imputation

### B: Imputation Preparation

Triggered by: "prepare for imputation", "I want to impute"

1. **Export VCF**: Generate imputation-ready VCF from SQLite
   ```bash
   python3 scripts/prepare_for_imputation.py
   ```
2. **REF/ALT normalization** (requires bcftools):
   ```bash
   bcftools norm --check-ref ws --fasta-ref hg19.fa output.vcf -o normalized.vcf
   ```
3. **Pre-upload checklist**:
   - [ ] VCF generated and validated
   - [ ] REF/ALT normalized against reference genome
   - [ ] Chromosome naming correct for target server
   - [ ] File compressed with bgzip (optional)
4. **Server guidance**: Show comparison table (Michigan vs TOPMed vs Sanger)
5. **Known gotchas**:
   - Michigan requires >= 20 samples (duplicate sample column as workaround)
   - HRC r1.1 for EUR, TOPMed r3 for diverse ancestry
   - Processing: 2-12 hours
   - Results encrypted, deleted after 7 days

### C: Post-Imputation Import

Triggered by: "import imputed data", user provides VCF files

1. **Locate imputed VCFs**: Check `data/output/imputed/` or ask user
2. **Import**: Run `python3 scripts/genome_init.py <vcf> --min-r2 0.3`
3. **Quality report**: Show r² distribution (high/good/moderate/low)
4. **Suggest**: Re-run PRS, check gap coverage, update gene notes

### D: Troubleshooting

Common issues and fixes:
- **Allele switches**: Run `bcftools norm --check-ref ws` before upload
- **Chromosome naming**: UCSC uses `chr1`, HRC expects bare `1`
- **20-sample minimum**: Duplicate sample column 20x in VCF header
- **Low overlap**: Check assembly match (GRCh37 vs GRCh38)

## Supported Providers
| Provider | Format | Assembly | Detection |
|----------|--------|----------|-----------|
| 23andMe v4/v5 | TSV (4 cols) | GRCh37 | "23andMe" in comments |
| AncestryDNA | TSV (5 cols) | GRCh37 | allele1/allele2 columns |
| MyHeritage | CSV (4 cols) | GRCh37 | "RSID,CHROMOSOME,POSITION,RESULT" |
| Nebula | VCF | from header | "source=Nebula" |
| Generic VCF | VCF | from header | "##fileformat=VCF" |

## Output
- Populated SQLite database with profile and import tracking
- QC report (console + optional markdown)
- Next step recommendations
