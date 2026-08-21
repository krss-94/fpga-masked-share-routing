"""
Milestone 0: Share Mapping Coverage measurement (v2).

Requires RapidWright (Java) accessed via JPype -- see
https://www.rapidwright.io for setup instructions.

Usage:
    python milestone0_coverage.py placed_routed.dcp \\
        --jar /path/to/rapidwright-standalone.jar

    (or set RAPIDWRIGHT_JAR environment variable instead of --jar)

Implements the metric frozen in Phase 13.0:

    Coverage = (physical objects assigned exactly one share)
               / (total relevant physical objects)

GRANULARITY (fixed for Milestone 0, per review):
    This script measures coverage at LOGICAL CELL granularity only.
    The methodology (Phase 11/12) leaves granularity configurable
    for later phases -- Milestone 0 does not attempt to validate
    that flexibility, only whether the mapping problem is tractable
    at the simplest possible unit. BEL/Site/Net-level granularity
    is future work, not attempted here.

HONESTY NOTE ON WHAT THIS SCRIPT ACTUALLY DOES:
    `infer_shares()` is a NAME-BASED HEURISTIC, not a share-ownership
    verifier. It reads a naming convention deliberately embedded in
    masked_and_gadget.v as test instrumentation for this benchmark.
    It does not inspect actual signal provenance, does not trace
    logic cones, and would silently fail on any design that doesn't
    follow this exact naming convention. This is acceptable for
    Milestone 0 -- whose job is only to check whether the mapping
    problem is tractable at all -- but this heuristic must NOT be
    mistaken for, or evolve unremarked into, the actual M2 Share
    Correlator design. M2 should exploit hierarchical netlist
    metadata directly where available; naming should serve only as
    a fallback or benchmark convenience, not the mechanism itself.

    Similarly, `categorize_mechanism()` is a HEURISTIC CLASSIFIER,
    not a mechanism detector. It guesses a plausible cause for an
    unmapped/ambiguous object from cell type and name patterns. It
    does not verify that guess against Vivado's actual optimization
    log. Treat its output as a debugging hint, not a scientific claim.
"""

import sys
import os
import re
import csv
import json
import argparse
from collections import defaultdict

import jpype
import jpype.imports


def start_rapidwright(jar_path: str):
    jpype.startJVM(classpath=[jar_path])


# --------------------------------------------------------------------
# Naming convention from masked_and_gadget.v. This is TEST
# INSTRUMENTATION specific to this benchmark artifact, not a general
# property the methodology depends on. See module docstring.
# --------------------------------------------------------------------

SHARE0_PATTERN = re.compile(r"(^|[_/])sh0([_/]|$)")
SHARE1_PATTERN = re.compile(r"(^|[_/])sh1([_/]|$)")
CROSS_PATTERN = re.compile(r"cross(01|10)")

CARRY_CELL_TYPES = {"CARRY4", "CARRY8"}
BUFFER_CELL_TYPES = {"BUFG", "BUFGCE", "BUFH", "BUFR", "OBUF", "IBUF"}


def infer_shares_heuristic(hier_name: str) -> set:
    """NAME-BASED HEURISTIC. See module docstring: this is share
    inference from a test-instrumentation naming convention, not
    share verification. Returns the set of shares (subset of {0, 1})
    a hierarchical name appears to touch."""
    shares = set()
    if SHARE0_PATTERN.search(hier_name):
        shares.add(0)
    if SHARE1_PATTERN.search(hier_name):
        shares.add(1)
    if CROSS_PATTERN.search(hier_name):
        shares.update({0, 1})
    return shares


def categorize_mechanism_heuristic(cell) -> str:
    """HEURISTIC CLASSIFIER, not a verified mechanism detector.
    Best-effort guess at *why* an object might be unmapped/ambiguous,
    from cell type and name pattern alone. Cross-check against
    post_route_drc.rpt / post_route_timing_summary.rpt manually
    before trusting this label."""
    cell_type = str(cell.getType()) if hasattr(cell, "getType") else ""
    name = str(cell.getName())

    if cell_type in CARRY_CELL_TYPES:
        return "carry_chain (heuristic)"
    if cell_type in BUFFER_CELL_TYPES:
        return "buffer_insertion (heuristic)"
    if re.search(r"_replica|_dup\d*$", name):
        return "driver_duplication_or_replication (heuristic)"
    if "LUT" in cell_type and CROSS_PATTERN.search(name) is None and (
        SHARE0_PATTERN.search(name) and SHARE1_PATTERN.search(name)
    ):
        return "lut_combining (heuristic)"
    return "unclassified (heuristic)"


def measure_coverage(dcp_path: str):
    from com.xilinx.rapidwright.design import Design  # noqa: E402

    design = Design.readCheckpoint(dcp_path)

    rows = []  # one row per logical cell: for coverage.csv
    total = 0
    exactly_one_share = 0
    unmapped = []
    ambiguous = []
    mechanism_tally = defaultdict(int)

    # --- Logical cells only. This is the fixed granularity for
    #     Milestone 0 -- see module docstring. ---
    for cell in design.getCells():
        total += 1
        hier_name = str(cell.getName())
        shares = infer_shares_heuristic(hier_name)

        if len(shares) == 0:
            status = "unmapped"
            mechanism = categorize_mechanism_heuristic(cell)
            unmapped.append(hier_name)
            mechanism_tally[mechanism] += 1
        elif len(shares) == 1:
            status = "mapped"
            mechanism = ""
            exactly_one_share += 1
        else:
            if not CROSS_PATTERN.search(hier_name):
                status = "ambiguous"
                mechanism = categorize_mechanism_heuristic(cell)
                ambiguous.append(hier_name)
                mechanism_tally[mechanism] += 1
            else:
                status = "mapped"  # expected cross-share gadget term
                mechanism = ""
                exactly_one_share += 1

        rows.append({
            "object": hier_name,
            "share": ",".join(str(s) for s in sorted(shares)) if shares else "",
            "status": status,
            "mechanism": mechanism,
        })

    coverage = exactly_one_share / total if total else 0.0

    report = {
        "dcp": dcp_path,
        "granularity": "logical_cell",
        "cell_coverage": {
            "total_cells": total,
            "exactly_one_share": exactly_one_share,
            "unmapped_count": len(unmapped),
            "ambiguous_count": len(ambiguous),
            "coverage_ratio": coverage,
        },
        "mechanism_tally_heuristic": dict(mechanism_tally),
    }
    return report, rows


def write_csv(rows, path="coverage.csv"):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["object", "share", "status", "mechanism"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Milestone 0 share mapping coverage")
    parser.add_argument("dcp", help="Path to placed_routed.dcp")
    parser.add_argument(
        "--jar",
        default=os.environ.get("RAPIDWRIGHT_JAR"),
        help="Path to RapidWright standalone jar (or set RAPIDWRIGHT_JAR env var)",
    )
    args = parser.parse_args()

    if not args.jar:
        print("Error: RapidWright jar path required via --jar or RAPIDWRIGHT_JAR env var.")
        sys.exit(1)

    start_rapidwright(args.jar)
    result, rows = measure_coverage(args.dcp)

    print(json.dumps(result, indent=2))
    with open("milestone0_coverage_report.json", "w") as f:
        json.dump(result, f, indent=2)

    # Per review: write the inspectable CSV BEFORE any graph-building
    # code exists. This is the artifact to manually eyeball for
    # mapping mistakes before touching M2.
    write_csv(rows, "coverage.csv")

    print("\n--- Result (granularity: logical cell; threshold X not yet set, per Phase 13.0) ---")
    print(f"Coverage: {result['cell_coverage']['coverage_ratio']:.2%}")
    print(f"Unmapped: {result['cell_coverage']['unmapped_count']}")
    print(f"Ambiguous: {result['cell_coverage']['ambiguous_count']}")
    print("\nSee coverage.csv for per-object detail (inspect before building M2).")
    print("Mechanism labels in this report are HEURISTIC GUESSES, not verified causes --")
    print("cross-check against post_route_drc.rpt and post_route_timing_summary.rpt.")
