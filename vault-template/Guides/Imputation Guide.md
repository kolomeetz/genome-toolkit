---
type: guide
created_date: '{{date}}'
tags:
  - guide
  - imputation
  - pipeline
---

# Imputation Guide

## What Is Imputation?

Your DTC genotyping array measures ~600K SNPs — roughly 1.5% of common human variation. **Imputation** uses statistical methods to infer the remaining ~40M common variants by leveraging linkage disequilibrium (LD) patterns from large reference panels.

If your array measured SNP A and SNP B, and a reference panel shows that SNP C between them almost always carries allele T when A=G and B=C, then you probably carry T at position C too.

### Why It Matters

| What It Unlocks | Before Imputation | After Imputation |
|----------------|-------------------|------------------|
| Polygenic Risk Scores | ~500 relevant SNPs | ~150K+ relevant SNPs |
| Rare variant detection | Limited | Fills gaps in gene regulatory regions |
| PGx coverage | Basic CYP haplotypes | Better haplotype resolution |
| HLA region | Sparse | Denser (but not definitive for HLA typing) |

### What It Cannot Do
- Structural variants and CNVs (e.g., CYP2D6 deletions) — requires sequencing
- Truly novel variants (de novo mutations)
- Low-frequency variants (MAF < 0.5%) — impute poorly
- Cross-ancestry: quality depends on reference panel ancestry match

## Step-by-Step Process

### 1. Prepare VCF
Run imputation preparation:
```
/genome-import prepare for imputation
```

This generates a VCF file from your imported data with QC filters applied.

### 2. Normalize REF/ALT (Important!)
```bash
bcftools norm --check-ref ws --fasta-ref hg19.fa output.vcf -o normalized.vcf
bcftools annotate --rename-chrs chr_rename.txt normalized.vcf -o final.vcf
```
Without this step, ~80K allele switches can occur.

### 3. Upload to Imputation Server

**Recommended: Michigan Imputation Server**
- URL: https://imputationserver.sph.umich.edu
- Free, encrypted, data deleted after 7 days
- Select: TOPMed r3 (diverse) or HRC r1.1 (European)
- Population: EUR (or Mixed if uncertain)
- Processing: 2-12 hours

### 4. Download and Decrypt
Results arrive as encrypted zip files (one per chromosome).
Decrypt with the server-provided password.

### 5. Import Imputed Data
```
/genome-import import imputed data
```
Or manually:
```bash
python3 scripts/genome_init.py data/output/imputed/chr1.dose.vcf.gz --min-r2 0.3
```

### 6. Quality Thresholds

| r² | Use Case | Typical Variants |
|----|----------|-----------------|
| > 0.9 | Gene notes, Reports | ~5-8M |
| > 0.8 | Standard analysis | ~10-15M |
| > 0.5 | PRS calculation | ~20-25M |
| > 0.3 | Exploratory | ~30-35M |

**Recommendation**: Import at r² > 0.3, but use r² > 0.8 for Gene notes and clinical Reports.

## Known Gotchas

1. **Always normalize REF/ALT** against the reference FASTA before upload
2. **Chromosome naming matters**: UCSC uses `chr1`, HRC expects bare `1`
3. **5-sample minimum**: Michigan server requires >= 5 samples per VCF (duplicate sample column as workaround)
4. **Assembly match**: Ensure your data is GRCh37 if using HRC, or check server requirements

## External Tools Required
- `bcftools` — `brew install bcftools` (macOS) / `apt install bcftools` (Linux)
- `bgzip`/`tabix` — `brew install htslib` (macOS) / `apt install tabix` (Linux)
- Reference genome — download `hg19.fa` from UCSC

## Privacy
- Servers use AES-256 encryption
- Data deleted after 7 days (Michigan) or 30 days (TOPMed)
- No data sharing with third parties
- Imputed data is still genomic data — keep in `data/` (gitignored)

## Timeline
| Step | Time |
|------|------|
| VCF preparation | 2 minutes |
| Upload | 5-15 minutes |
| Server processing | 2-12 hours |
| Download + decrypt | 10-30 minutes |
| Import | 5-15 minutes |
| **Total** | **~3-13 hours** (mostly waiting) |
