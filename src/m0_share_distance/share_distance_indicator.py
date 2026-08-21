"""
Simplified M3 + M4: Share-Distance Indicator (v1, "perimeter" scope)

This is the scoped-down M3/M4 agreed for the semester deliverable:
  - ONE relationship considered: physical distance between share-0 and
    share-1 objects (the "resource-sharing" edge type from the original
    Phase 12 plan is explicitly NOT built here -- future work).
  - ONE indicator: minimum and mean Manhattan tile-distance between every
    share-0 / share-1 object pair.
  - NO fusion (M5/M6). This script reports the raw indicator per gadget.
    Combining it with proof-flagged-independence claims is future work.

It reuses the already-validated `infer_shares_heuristic()` from
milestone0_coverage.py rather than re-implementing share inference, so
the two scripts stay consistent with each other and with the manually
inspected coverage.csv files for each gadget.

HONESTY NOTE:
    "Distance" here is FPGA tile-grid Manhattan distance, not physical
    microns, not routing delay, and not a validated leakage predictor.
    It is a simple, inspectable proxy: closer tiles are a plausible (not
    proven) risk signal, consistent with the "does coupling affect
    security" line of prior work cited during this project's novelty
    check. Treat this as a first, defensible data point -- not a
    leakage verdict.

Usage:
    python share_distance_indicator.py placed_routed.dcp \\
        --jar /path/to/rapidwright-standalone.jar \\
        --label and_gadget

Run once per gadget (pointing at each gadget's own placed_routed.dcp),
then compare the resulting distance_indicator_<label>.json files by hand.
"""

import os
import sys
import json
import csv
import argparse

from milestone0_coverage import start_rapidwright, infer_shares_heuristic


# ALLOWLIST, not blacklist (v3). The v2 blacklist (BUFFER_CELL_TYPES)
# missed a real confound: RapidWright's design.getCells() returned a
# port pass-through object (e.g. "a_sh1", "b_sh0") that is NOT a real
# implemented cell -- confirmed via Vivado's own `get_cells -hierarchical
# *a_sh1*`, which only found "a_sh1_IBUF_inst", never a bare "a_sh1"
# cell. Yet this pass-through object had a valid site (skipped_no_coords
# was 0), almost certainly because it's physically pinned to the exact
# same site as its IBUF -- reintroducing the I/O-pad confound v2 was
# supposed to remove, just under a name the v2 blacklist didn't know to
# exclude.
#
# Rather than keep guessing new blacklist entries every time a new kind
# of non-logic object shows up, v3 flips the logic: only cell TYPES that
# are genuine computational primitives are included. Anything else is
# excluded by default, known or not.
CORE_LOGIC_EXACT_TYPES = {
    "FDRE", "FDSE", "FDCE", "FDPE",
    "FDRE_1", "FDSE_1", "FDCE_1", "FDPE_1",
    "CARRY4", "CARRY8",
}


def is_core_logic(cell_type: str) -> bool:
    if cell_type.startswith("LUT"):
        return True
    return cell_type in CORE_LOGIC_EXACT_TYPES


def get_tile_coords(cell):
    """Best-effort extraction of physical (column, row) tile coordinates
    for a placed cell, via RapidWright's Cell -> Site -> Tile chain.

    Returns None if the cell has no physical site (e.g. optimized away,
    or a non-leaf/hierarchical cell) -- these are counted and reported
    separately, never silently dropped.

    NOTE: this assumes RapidWright's Cell.getSite() / Site.getTile() /
    Tile.getColumn() / Tile.getRow() API. If this raises an error on
    your RapidWright version, that's a real, expected debugging step --
    paste the traceback and we adjust to the actual API surface.
    """
    try:
        site = cell.getSite()
    except Exception:
        return None
    if site is None:
        return None
    try:
        tile = site.getTile()
        return (int(tile.getColumn()), int(tile.getRow()))
    except Exception:
        return None


def build_share_points(dcp_path):
    from com.xilinx.rapidwright.design import Design  # noqa: E402

    design = Design.readCheckpoint(dcp_path)

    share0_points = []
    share1_points = []
    skipped_no_coords = 0
    skipped_not_single_share = 0

    skipped_io_buffer = 0
    debug_rows = []
    for cell in design.getCells():
        hier_name = str(cell.getName())
        shares = infer_shares_heuristic(hier_name)
        cell_type = str(cell.getType()) if hasattr(cell, "getType") else ""

        # Only single-share objects go into the distance calculation.
        # Cross-share terms, randomness, and clock/IO infrastructure are
        # excluded by design -- see each gadget's notes.md for why each
        # excluded category is legitimate to skip (same reasoning as the
        # coverage.csv manual inspection already done for gadgets 1-3).
        if len(shares) != 1:
            skipped_not_single_share += 1
            debug_rows.append((hier_name, cell_type, "skipped_not_single_share"))
            continue

        # v3: allowlist genuine computational logic types only (see
        # module-level comment for why this replaced the v2 blacklist).
        if not is_core_logic(cell_type):
            skipped_io_buffer += 1
            debug_rows.append((hier_name, cell_type, "skipped_non_core_logic"))
            continue

        coords = get_tile_coords(cell)
        if coords is None:
            skipped_no_coords += 1
            debug_rows.append((hier_name, cell_type, "skipped_no_coords"))
            continue

        share = next(iter(shares))
        debug_rows.append((hier_name, cell_type, f"kept_share{share}"))
        if share == 0:
            share0_points.append((hier_name, coords))
        else:
            share1_points.append((hier_name, coords))

    return share0_points, share1_points, skipped_no_coords, skipped_not_single_share, skipped_io_buffer, debug_rows


def manhattan(p, q):
    return abs(p[0] - q[0]) + abs(p[1] - q[1])


def compute_distance_indicator(share0_points, share1_points):
    """The single M4 indicator for this scoped version: for every
    share-0 / share-1 object pair, compute Manhattan tile distance.
    Report the minimum (closest approach -- the most security-relevant
    number, since an attacker cares about the closest two shares ever
    get physically) and the mean (overall separation trend)."""
    if not share0_points or not share1_points:
        return {
            "pairs_considered": 0,
            "min_distance": None,
            "mean_distance": None,
            "closest_pair": None,
        }

    min_dist = None
    min_pair = None
    total = 0
    count = 0

    for name0, p0 in share0_points:
        for name1, p1 in share1_points:
            d = manhattan(p0, p1)
            total += d
            count += 1
            if min_dist is None or d < min_dist:
                min_dist = d
                min_pair = (name0, name1)

    return {
        "pairs_considered": count,
        "min_distance": min_dist,
        "mean_distance": total / count if count else None,
        "closest_pair": min_pair,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Simplified M3+M4: share-distance indicator from a placed_routed.dcp"
    )
    parser.add_argument("dcp", help="Path to placed_routed.dcp")
    parser.add_argument(
        "--jar",
        default=os.environ.get("RAPIDWRIGHT_JAR"),
        help="Path to RapidWright standalone jar (or set RAPIDWRIGHT_JAR env var)",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="Optional label for this gadget (e.g. 'and_gadget'), used in output filename",
    )
    args = parser.parse_args()

    if not args.jar:
        print("Error: RapidWright jar path required via --jar or RAPIDWRIGHT_JAR env var.")
        sys.exit(1)

    start_rapidwright(args.jar)
    share0_points, share1_points, skipped_no_coords, skipped_not_single_share, skipped_io_buffer, debug_rows = build_share_points(args.dcp)
    indicator = compute_distance_indicator(share0_points, share1_points)

    report = {
        "dcp": args.dcp,
        "label": args.label,
        "share0_object_count": len(share0_points),
        "share1_object_count": len(share1_points),
        "skipped_no_coords": skipped_no_coords,
        "skipped_not_single_share": skipped_not_single_share,
        "skipped_non_core_logic": skipped_io_buffer,
        "note": "v3: allowlist genuine core-logic cell types (LUT*/FDRE/FDSE/FDCE/FDPE/CARRY4/CARRY8) instead of blacklisting known IO/buffer types -- see module docstring for why v2's blacklist missed a port pass-through confound.",
        "distance_indicator": indicator,
    }

    print(json.dumps(report, indent=2))

    out_name = f"distance_indicator_{args.label}.json" if args.label else "distance_indicator.json"
    with open(out_name, "w") as f:
        json.dump(report, f, indent=2)

    debug_out_name = f"distance_indicator_debug_{args.label}.csv" if args.label else "distance_indicator_debug.csv"
    with open(debug_out_name, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["object", "cell_type", "decision"])
        writer.writerows(debug_rows)

    print(f"\nWritten: {out_name}")
    print(f"Written: {debug_out_name} (per-object inspection trail -- check this")
    print("before trusting the indicator, same discipline as coverage.csv)")
    print("NOTE: distance is in FPGA tile-grid units (Manhattan), not physical")
    print("microns or routing delay. This is a relative, comparative indicator")
    print("across gadgets on the SAME device (xc7a100tcsg324-1), not an")
    print("absolute or validated leakage measure.")
