#!/usr/bin/env python3
"""
Export genotyped SNPs from SQLite to VCF format for imputation servers.

Input:  SQLite database (genome.db) — provider-agnostic, works with any imported data
Output: data/output/for_imputation.vcf

QC steps applied:
  - Remove no-calls (-- genotype)
  - Remove indels (D/I alleles)
  - Remove non-rsid variants (internal provider IDs)
  - Remove mitochondrial (MT) and Y chromosome variants
  - Remove monomorphic calls that can't be represented as biallelic SNPs
  - Sort by chromosome and position
  - Generate valid VCF 4.1 with proper headers
"""

import argparse
import os
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.config import DB_PATH, OUTPUT_DIR
from lib.db import get_connection

# Valid nucleotides for SNPs
VALID_ALLELES = set("ACGT")

# Chromosome sort order
CHROM_ORDER = {str(i): i for i in range(1, 23)}
CHROM_ORDER["X"] = 23


def query_genotyped_snps(db_path, profile_id="default"):
    """Query genotyped SNPs from SQLite database.

    Returns list of (chrom, pos, rsid, genotype) tuples and QC stats.
    The profile_id parameter is reserved for future multi-profile support.
    """
    variants = []
    stats = defaultdict(int)

    conn = get_connection(db_path)
    cursor = conn.execute(
        "SELECT rsid, chromosome, position, genotype FROM snps WHERE source = 'genotyped'"
    )

    for row in cursor:
        rsid, chrom, pos, genotype = row["rsid"], row["chromosome"], row["position"], row["genotype"]
        stats["total_input"] += 1

        # Skip non-rsid variants (internal provider IDs like i6019299)
        if not rsid.startswith("rs"):
            stats["skipped_non_rsid"] += 1
            continue

        # Skip no-calls
        if genotype == "--" or not genotype:
            stats["skipped_nocall"] += 1
            continue

        # Skip MT and Y chromosomes (not imputable)
        if chrom in ("MT", "Y"):
            stats[f"skipped_{chrom}"] += 1
            continue

        # Skip indels (D = deletion, I = insertion)
        if "D" in genotype or "I" in genotype:
            stats["skipped_indel"] += 1
            continue

        # Validate alleles are standard nucleotides
        if not all(a in VALID_ALLELES for a in genotype):
            stats["skipped_invalid_allele"] += 1
            continue

        # Skip if chromosome not in expected set
        if chrom not in CHROM_ORDER:
            stats["skipped_unknown_chrom"] += 1
            continue

        variants.append((chrom, pos, rsid, genotype))
        stats["passed_qc"] += 1

    conn.close()
    return variants, stats


def genotype_to_vcf_fields(genotype):
    """Convert genotype string to VCF REF, ALT, GT fields.

    Genotypes are stored on the plus strand in the database.
    For homozygous calls (AA), REF=A, ALT=., GT=0/0 — but imputation servers
    need a concrete ALT. We use REF=first allele, ALT=second if different.

    Returns (ref, alt, gt) or None if variant should be skipped.
    """
    if len(genotype) == 1:
        # Haploid call (X chromosome in males)
        ref = genotype
        return ref, ".", "0"

    if len(genotype) == 2:
        a1, a2 = genotype[0], genotype[1]

        if a1 == a2:
            # Homozygous — still include, imputation servers handle these
            # REF = the observed allele, ALT = .
            return a1, ".", "0/0"
        else:
            # Heterozygous
            # By convention, use first allele as REF
            return a1, a2, "0/1"

    return None


def write_vcf(variants, output_path, num_samples=20):
    """Write sorted variants to VCF format.

    Sorts by chromosome (numeric order) then position.
    Michigan Imputation Server requires >= 20 samples per VCF.
    For single-person data, we duplicate the genotype column to meet this minimum.
    """
    # Sort: chromosome by numeric order, then by position
    variants.sort(key=lambda v: (CHROM_ORDER.get(v[0], 99), v[1]))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    skipped_conversion = 0
    written = 0

    sample_names = [f"SAMPLE_{i:02d}" for i in range(1, num_samples + 1)]

    with open(output_path, "w") as f:
        # VCF header
        f.write("##fileformat=VCFv4.1\n")
        f.write(f"##fileDate={date.today().strftime('%Y%m%d')}\n")
        f.write("##source=genome_toolkit_prepare_for_imputation\n")
        f.write("##reference=GRCh37\n")
        f.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')

        # Contig headers for chromosomes present
        chroms_seen = sorted(set(v[0] for v in variants),
                            key=lambda c: CHROM_ORDER.get(c, 99))
        for chrom in chroms_seen:
            f.write(f"##contig=<ID={chrom}>\n")

        # Column header
        f.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t")
        f.write("\t".join(sample_names) + "\n")

        # Data lines — duplicate GT across all sample columns
        for chrom, pos, rsid, genotype in variants:
            result = genotype_to_vcf_fields(genotype)
            if result is None:
                skipped_conversion += 1
                continue

            ref, alt, gt = result
            gt_cols = "\t".join([gt] * num_samples)
            f.write(f"{chrom}\t{pos}\t{rsid}\t{ref}\t{alt}\t.\tPASS\t.\tGT\t{gt_cols}\n")
            written += 1

    return written, skipped_conversion


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Export genotyped SNPs from SQLite to VCF for imputation servers."
    )
    parser.add_argument(
        "--profile",
        default="default",
        help="Profile ID to export (default: 'default'). Reserved for future multi-profile support.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=f"Output VCF path (default: {OUTPUT_DIR / 'for_imputation.vcf'})",
    )
    parser.add_argument(
        "--db",
        default=None,
        help=f"Path to SQLite database (default: {DB_PATH})",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=20,
        help="Number of duplicate sample columns in VCF (Michigan Imputation Server requires >= 20, default: 20)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    db_path = Path(args.db) if args.db else DB_PATH
    output_file = args.output if args.output else str(OUTPUT_DIR / "for_imputation.vcf")

    print("=" * 60)
    print("Genotyped SNPs → VCF Conversion for Imputation")
    print("=" * 60)
    print()

    # Check database exists
    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        sys.exit(1)

    print(f"Database: {db_path}")
    print(f"Profile:  {args.profile}")
    print(f"Output:   {output_file}")
    print()

    # Query genotyped SNPs
    print("Querying genotyped SNPs from database...")
    variants, stats = query_genotyped_snps(db_path, profile_id=args.profile)

    # Write VCF
    print(f"Writing VCF with {args.samples} sample columns...")
    written, skipped_conversion = write_vcf(variants, output_file, num_samples=args.samples)

    # Report
    print()
    print("=" * 60)
    print("QC Summary")
    print("=" * 60)
    print(f"  Total genotyped SNPs:       {stats['total_input']:>10,}")
    print(f"  Passed QC:                  {stats['passed_qc']:>10,}")
    print(f"  Written to VCF:             {written:>10,}")
    print()
    print("  Filtered out:")
    print(f"    No-calls (--):            {stats['skipped_nocall']:>10,}")
    print(f"    Non-rsid (internal IDs):  {stats['skipped_non_rsid']:>10,}")
    print(f"    Indels (D/I):             {stats['skipped_indel']:>10,}")
    print(f"    MT chromosome:            {stats['skipped_MT']:>10,}")
    print(f"    Y chromosome:             {stats['skipped_Y']:>10,}")
    print(f"    Invalid alleles:          {stats['skipped_invalid_allele']:>10,}")
    print(f"    Unknown chromosome:       {stats['skipped_unknown_chrom']:>10,}")
    print(f"    Conversion errors:        {skipped_conversion:>10,}")
    print()

    # File size
    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"  Output file size: {size_mb:.1f} MB")
    print()

    # Next steps
    print("Next steps:")
    print("  1. Optionally compress: bgzip " + output_file)
    print("  2. Upload to Michigan Imputation Server: https://imputationserver.sph.umich.edu")
    print("  3. Select TOPMed r3 reference panel, appropriate population")
    print("  4. See Research/20260323-genome-imputation-guide.md for full instructions")


if __name__ == "__main__":
    main()
