#!/usr/bin/env python3
"""
extract_conflict_pips.py -- Milestone 4 input generator.

Takes a routed DCP + the switchbox_conflicts.csv produced by
switchbox_conflict_detector.py, and for each conflict row finds the
SPECIFIC PIP-level nodes (tile/wire) that each of the two conflicting
nets actually used inside the shared switch-box tile.

This is the missing link between Milestone 1 (which only records the
CONFLICT TILE, not which wires inside it) and the Milestone 4 patched
RWRoute.java (which needs RWROUTE_FORBIDDEN_NODES as a TILE/WIRE list,
not a tile list).

USAGE (same pattern as your other milestone scripts):

    python extract_conflict_pips.py and_gadget_xczu2_hardexcl_routed.dcp ^
        --jar %RAPIDWRIGHT_JAR% ^
        --conflicts switchbox_conflicts.csv ^
        --out forbidden_nodes.txt

OUTPUT:
    - Prints a human-readable breakdown per conflict row to stdout.
    - Writes forbidden_nodes.txt: one TILE/WIRE per line, deduplicated.
    - Also prints a single line ready to paste directly into:
          set RWROUTE_FORBIDDEN_NODES=TILE/WIRE,TILE/WIRE,...

NOTE ON co_located_terminal conflicts (if your CSV has a conflict_type
column): these are skipped by default and reported separately, since
per the Milestone 1 detector's own note, a conflict where the shared
tile is a net's own source/sink tile can't be avoided by forbidding
any node -- the node the patch would need to forbid IS the net's own
endpoint, which Milestone 4's exemption logic already lets through
regardless. Forbidding it would just silently do nothing. Use --include-terminal
to include them anyway (e.g. for completeness in a report), but don't
expect them to change routing behavior.
"""

import argparse
import csv
import sys
from collections import defaultdict


def start_rapidwright(jar_path):
    import jpype
    import jpype.imports  # noqa: F401 -- required to enable `from com.xilinx... import X` syntax
    if not jpype.isJVMStarted():
        jpype.startJVM(classpath=[jar_path])


def load_conflicts(csv_path):
    """Returns list of dicts: tile, share0_net, share1_net, conflict_type (or None)."""
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        has_type = "conflict_type" in (reader.fieldnames or [])
        for row in reader:
            rows.append({
                "tile": row["tile"],
                "share0_net": row["share0_net"],
                "share1_net": row["share1_net"],
                "conflict_type": row.get("conflict_type") if has_type else None,
            })
    return rows


def nodes_of_net_in_tile(net, tile_name):
    """
    Walks every PIP of `net` and returns the set of "TILE/WIRE" strings
    (start wire and end wire of each PIP) whose tile matches tile_name.

    This mirrors exactly how the Milestone 4 RWRoute.java patch builds
    its own node key: childRNode.getTile().getName() + "/" + childRNode.getWireName()
    -- so entries emitted here will match verbatim against what the
    patched router checks during search.
    """
    found = set()
    for pip in net.getPIPs():
        pip_tile = pip.getTile()
        pip_tile_name = str(pip_tile.getName())
        if pip_tile_name != tile_name:
            continue
        start_wire = pip.getStartWireName()
        end_wire = pip.getEndWireName()
        if start_wire:
            found.add(f"{pip_tile_name}/{start_wire}")
        if end_wire:
            found.add(f"{pip_tile_name}/{end_wire}")
    return found


def analyze(dcp_path, conflicts_csv, include_terminal):
    from com.xilinx.rapidwright.design import Design  # noqa: E402

    print(f"Reading DCP: {dcp_path}")
    design = Design.readCheckpoint(dcp_path)

    conflicts = load_conflicts(conflicts_csv)
    print(f"Loaded {len(conflicts)} conflict row(s) from {conflicts_csv}\n")

    all_forbidden_nodes = set()
    skipped_terminal = 0
    skipped_no_pips_in_tile = []

    net_cache = {}

    def get_net(name):
        if name not in net_cache:
            net_cache[name] = design.getNet(name)
        return net_cache[name]

    for i, row in enumerate(conflicts, 1):
        tile = row["tile"]
        n0_name = row["share0_net"]
        n1_name = row["share1_net"]
        ctype = row["conflict_type"]

        if ctype == "co_located_terminal" and not include_terminal:
            skipped_terminal += 1
            print(f"[{i}] {tile}: {n0_name} <-> {n1_name}  (co_located_terminal -- SKIPPED, see docstring)")
            continue

        n0 = get_net(n0_name)
        n1 = get_net(n1_name)
        if n0 is None or n1 is None:
            print(f"[{i}] {tile}: WARNING -- could not find net object for "
                  f"'{n0_name if n0 is None else n1_name}' in design, skipping")
            continue

        n0_nodes = nodes_of_net_in_tile(n0, tile)
        n1_nodes = nodes_of_net_in_tile(n1, tile)
        this_row_nodes = n0_nodes | n1_nodes

        if not this_row_nodes:
            skipped_no_pips_in_tile.append((tile, n0_name, n1_name))
            print(f"[{i}] {tile}: {n0_name} <-> {n1_name}  "
                  f"WARNING -- no PIPs of either net found in this tile (unexpected, inspect manually)")
            continue

        print(f"[{i}] {tile}: {n0_name} <-> {n1_name}"
              + ("  [co_located_terminal, included via --include-terminal]" if ctype == "co_located_terminal" else ""))
        for node in sorted(this_row_nodes):
            print(f"      {node}")

        all_forbidden_nodes.update(this_row_nodes)

    print()
    print(f"--- Summary ---")
    print(f"Conflict rows processed:      {len(conflicts) - skipped_terminal}")
    print(f"co_located_terminal skipped:  {skipped_terminal}")
    if skipped_no_pips_in_tile:
        print(f"Rows with NO PIPs found in tile (needs manual check): {len(skipped_no_pips_in_tile)}")
    print(f"Total unique forbidden nodes: {len(all_forbidden_nodes)}")

    return sorted(all_forbidden_nodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dcp", help="Routed DCP to read nets/PIPs from")
    parser.add_argument("--jar", required=True, help="Path to rapidwright-standalone jar")
    parser.add_argument("--conflicts", required=True, help="switchbox_conflicts.csv from Milestone 1")
    parser.add_argument("--out", default="forbidden_nodes.txt", help="Output file (one TILE/WIRE per line)")
    parser.add_argument("--include-terminal", action="store_true",
                         help="Also emit nodes for co_located_terminal conflicts (see docstring -- these won't "
                              "actually change routing behavior, included only for completeness)")
    args = parser.parse_args()

    start_rapidwright(args.jar)
    forbidden_nodes = analyze(args.dcp, args.conflicts, args.include_terminal)

    with open(args.out, "w") as f:
        for node in forbidden_nodes:
            f.write(node + "\n")
    print(f"\nWrote {len(forbidden_nodes)} forbidden node(s) to {args.out}")

    if forbidden_nodes:
        env_line = ",".join(forbidden_nodes)
        print("\nPaste this directly into your shell before running the Milestone 4 RWRoute:\n")
        print(f"set RWROUTE_FORBIDDEN_NODES={env_line}")
    else:
        print("\nNo forbidden nodes to emit -- nothing to paste. Check the warnings above.")


if __name__ == "__main__":
    main()
