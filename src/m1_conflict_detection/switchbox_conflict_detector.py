"""
Switch-Box Conflict Detector (Milestone 1).

MOTIVATION (see Mueller/Lammers/Osterheider/Moradi, IACR ePrint 2026/1426,
"Coupling Leakage in Theory and Practice"): physical tile-distance between
masked shares (Milestone 0's share_distance_indicator.py) does NOT guarantee
absence of coupling leakage. Their paper shows coupling occurs when wires
from different shares are routed through the SAME SWITCH BOX, regardless of
the tile-grid distance between the logic cells that own those wires. Their
mitigation process (Section 4.3, 5.1) is entirely MANUAL: identify each
violating switch box by hand, unroute, manually re-route, re-verify with
PROLEAD, repeat.

THIS SCRIPT'S CONTRIBUTION: automate the *detection* half of that process.
Instead of manually inspecting the routed design, this script:
  1. Reads a placed-and-routed DCP via RapidWright.
  2. For every net, determines its share-domain via the same naming-
     convention heuristic used in milestone0_coverage.py (test
     instrumentation, not a general mechanism -- see that script's docstring
     for the same caveat, which applies identically here).
  3. Walks every PIP used by every net and records which TILE (switch box)
     it passes through.
  4. Builds a conflict graph: an edge exists between two nets if they share
     at least one tile. This is the FPGA analogue of a crosstalk conflict
     graph in ASIC crosstalk-aware routing (e.g. CARRA -- Crosstalk-Aware
     Routing Resource Assignment), just applied to a fixed discrete switch
     fabric instead of continuous ASIC routing tracks.
  5. Flags any edge connecting a share-0-only net to a share-1-only net as
     a CROSS-SHARE SWITCH-BOX CONFLICT -- a candidate coupling-leakage site
     per the robust probing model's coupling extension (Faust et al. 2018,
     as used by Mueller et al. 2026).

WHAT THIS SCRIPT DOES NOT DO (explicit, same discipline as Milestone 0):
  - Does not run PROLEAD or any formal probing-security verification. A
    flagged conflict is a *candidate* coupling-leakage site, not a proven
    leak -- same "risk indicator, not proof" framing as Milestone 0.
  - Does not perform any automated re-routing or mitigation. Milestone 1
    is detection-only; automated mitigation (a security-aware router) is
    explicitly future work, same as it is in the Mueller et al. paper.
  - Does not model which specific wires *within* a shared switch box
    actually couple (capacitive vs inductive, physical PIP adjacency
    within the switch box). Like Mueller et al.'s own model, this is a
    conservative, worst-case abstraction: ANY two nets sharing a tile are
    flagged, regardless of which specific PIPs within that tile they use.
    This is the same worst-case simplification the source paper uses and
    explicitly defends (Section 4.2.1) for the same reason: precise
    intra-switch-box wire adjacency requires physical layout data (GDSII)
    that is not available for commercial FPGAs.

USAGE:
    python switchbox_conflict_detector.py placed_routed.dcp \\
        --jar /path/to/rapidwright-standalone.jar

    (or set RAPIDWRIGHT_JAR environment variable instead of --jar)

KNOWN UNCERTAINTY -- READ BEFORE RUNNING:
    The exact RapidWright method names for walking a Net's PIPs and getting
    a PIP's containing Tile are believed correct as of recent RapidWright
    versions (Net.getPIPs() -> List<PIP>; PIP.getTile() -> Tile;
    Tile.getName() -> String) but have NOT been verified against your
    installed RapidWright jar in this environment (no RapidWright/Vivado
    access here). If you get an AttributeError or a JPype method-not-found
    error on first run, paste the exact error back -- it is very likely a
    one-line method-name fix, not a design problem.
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
    classpath = jar_path.split(";")
    jpype.startJVM(classpath=classpath)

# --------------------------------------------------------------------
# Same naming-convention heuristic as milestone0_coverage.py, reused
# verbatim for consistency between Milestone 0 and Milestone 1 results.
# This is TEST INSTRUMENTATION specific to the masked_and_gadget.v /
# masked_xor_gadget.v / masked_nand_gadget.v benchmark artifacts, not a
# general property the methodology depends on.
# --------------------------------------------------------------------

SHARE0_PATTERN = re.compile(r"(^|[_/])sh0([_/]|$)")
SHARE1_PATTERN = re.compile(r"(^|[_/])sh1([_/]|$)")
CROSS_PATTERN = re.compile(r"cross(01|10)")


def infer_shares_heuristic(net_name: str) -> set:
    """NAME-BASED HEURISTIC. Identical logic to milestone0_coverage.py's
    infer_shares_heuristic, applied here to NET names instead of CELL
    names. Returns the set of shares (subset of {0, 1}) a net name appears
    to touch."""
    shares = set()
    if SHARE0_PATTERN.search(net_name):
        shares.add(0)
    if SHARE1_PATTERN.search(net_name):
        shares.add(1)
    if CROSS_PATTERN.search(net_name):
        shares.update({0, 1})
    return shares


def get_net_terminal_tiles(net) -> set:
    """Returns the set of routing-fabric-side tile names for every physical
    ENDPOINT (source + all sinks) of this net -- i.e. where the net's
    PIP-based route actually terminates, as opposed to tiles it merely
    passes through in open fabric.

    API confirmed empirically against the project's installed RapidWright
    jar via api_probe.py (2026): SitePinInst.getConnectedNode().getTile()
    gives the fabric-side tile a site pin connects into (e.g. INT_X15Y89),
    which is NOT the same as SitePinInst.getTile() (the CLB/site tile
    itself, e.g. CLEL_L_X15Y89). A net may have MULTIPLE sink pins (e.g.
    fanout to two different gadget cells), so this returns a set, not a
    single tile -- do not assume one sink per net.

    If this fails against a different RapidWright jar version, rerun
    api_probe.py against that jar and adjust accordingly; this is the
    same "believed correct, verify against your jar" caveat the rest of
    this script already carries.
    """
    terminal_tiles = set()

    source_pin = net.getSource()
    if source_pin is not None:
        try:
            terminal_tiles.add(str(source_pin.getConnectedNode().getTile().getName()))
        except Exception:
            pass  # static-driven or unusual source; skip rather than crash the whole run

    for sink_pin in net.getSinkPins():
        try:
            terminal_tiles.add(str(sink_pin.getConnectedNode().getTile().getName()))
        except Exception:
            pass

    return terminal_tiles


def build_tile_to_nets_map(design):
    """Walks every net in the design, records which tiles (switch boxes)
    its PIPs pass through. Returns:
        tile_to_nets: dict tile_name -> list of net_name
        net_shares:   dict net_name -> share-set (from naming heuristic)
        net_pip_count: dict net_name -> number of PIPs used by that net
            (diagnostic only -- nets with 0 PIPs are typically intra-site
            or unrouted; logged, not silently dropped)
        net_terminal_tiles: dict net_name -> set of tile names where this
            net's source/sink pins physically connect into the routing
            fabric (see get_net_terminal_tiles). Used to distinguish a
            conflict tile that is genuinely open mid-route fabric from one
            that is simply where two nets happen to terminate (e.g. both
            feed the same cross-share gadget cell) -- see
            find_cross_share_conflicts.
    """
    tile_to_nets = defaultdict(set)
    net_shares = {}
    net_pip_count = {}
    net_terminal_tiles = {}

    for net in design.getNets():
        net_name = str(net.getName())
        shares = infer_shares_heuristic(net_name)
        net_shares[net_name] = shares

        pips = net.getPIPs()
        net_pip_count[net_name] = len(pips)
        net_terminal_tiles[net_name] = get_net_terminal_tiles(net)

        seen_tiles_this_net = set()
        for pip in pips:
            tile = pip.getTile()
            tile_name = str(tile.getName())
            if tile_name not in seen_tiles_this_net:
                tile_to_nets[tile_name].add(net_name)
                seen_tiles_this_net.add(tile_name)

    return tile_to_nets, net_shares, net_pip_count, net_terminal_tiles


def find_cross_share_conflicts(tile_to_nets, net_shares, net_terminal_tiles=None):
    """For every tile used by more than one net, check whether it is used
    by a pure-share-0 net AND a pure-share-1 net (a candidate coupling
    site per the switch-box coupling model). Nets whose heuristic share-set
    is empty (no share tag matched -- e.g. clock, reset, unrelated control
    nets) or is {0,1} (a genuine cross-share gadget net, expected to touch
    both domains) are excluded from conflict flagging, same treatment
    milestone0_coverage.py gives to "expected cross-share gadget term"
    cells.

    conflict_type classification (added -- distinguishes two structurally
    different situations that a pure tile-sharing check conflates):
      "open_fabric": the shared tile is general routing fabric that both
          nets merely PASS THROUGH. This is the genuine candidate-leak
          case the Mueller et al. model targets -- two independently
          routed wires happening to cross the same switch box.
      "co_located_terminal": the shared tile is a TERMINAL tile (source or
          sink) for BOTH nets -- i.e. they don't just cross paths there,
          they physically end there (e.g. two share-tagged nets that both
          feed the same cross-share gadget cell, such as u_and_cross01/
          u_and_cross10 in the AND gadget). This is not a wire-to-wire
          coupling event in open fabric; it is the gadget's own
          cross-share computation happening at its designed location, and
          it cannot be avoided by ANY routing strategy since the cell's
          physical site does not move. Confirmed empirically: this
          matches, tile-for-tile, the two forbidden tiles that RWRoute's
          own hard-exclusion source/sink exemption logged as unavoidable
          in Milestone 3b (see EXEMPTED forbidden tile ... SINK tile logs).

    If net_terminal_tiles is None (old call signature), every conflict is
    classified as "open_fabric" and none as "co_located_terminal" -- this
    keeps the function backward-compatible, but callers should pass
    net_terminal_tiles (from build_tile_to_nets_map) to get the real split.

    Returns a list of conflict records, each:
        {"tile": ..., "share0_net": ..., "share1_net": ..., "conflict_type": ...}
    """
    if net_terminal_tiles is None:
        net_terminal_tiles = {}

    conflicts = []
    for tile_name, nets_in_tile in tile_to_nets.items():
        if len(nets_in_tile) < 2:
            continue

        share0_nets = [n for n in nets_in_tile if net_shares.get(n) == {0}]
        share1_nets = [n for n in nets_in_tile if net_shares.get(n) == {1}]

        if share0_nets and share1_nets:
            for n0 in share0_nets:
                for n1 in share1_nets:
                    n0_terminal = tile_name in net_terminal_tiles.get(n0, set())
                    n1_terminal = tile_name in net_terminal_tiles.get(n1, set())
                    conflict_type = "co_located_terminal" if (n0_terminal and n1_terminal) else "open_fabric"
                    conflicts.append({
                        "tile": tile_name,
                        "share0_net": n0,
                        "share1_net": n1,
                        "conflict_type": conflict_type,
                    })

    return conflicts


def analyze(dcp_path: str):
    from com.xilinx.rapidwright.design import Design  # noqa: E402

    design = Design.readCheckpoint(dcp_path)

    tile_to_nets, net_shares, net_pip_count, net_terminal_tiles = build_tile_to_nets_map(design)
    conflicts = find_cross_share_conflicts(tile_to_nets, net_shares, net_terminal_tiles)

    open_fabric_conflicts = [c for c in conflicts if c["conflict_type"] == "open_fabric"]
    co_located_conflicts = [c for c in conflicts if c["conflict_type"] == "co_located_terminal"]

    total_nets = len(net_shares)
    share0_only = sum(1 for s in net_shares.values() if s == {0})
    share1_only = sum(1 for s in net_shares.values() if s == {1})
    cross_share = sum(1 for s in net_shares.values() if s == {0, 1})
    unmatched = sum(1 for s in net_shares.values() if len(s) == 0)

    zero_pip_nets = [n for n, c in net_pip_count.items() if c == 0]

    report = {
        "dcp": dcp_path,
        "method": "switch_box_conflict_detector (Milestone 1)",
        "net_classification": {
            "total_nets": total_nets,
            "share0_only": share0_only,
            "share1_only": share1_only,
            "cross_share_expected": cross_share,
            "unmatched_no_share_tag": unmatched,
        },
        "diagnostics": {
            "zero_pip_net_count": len(zero_pip_nets),
            "note": (
                "zero_pip_net_count counts nets with no PIPs recorded "
                "(commonly intra-SLICE/intra-site connections that don't "
                "leave the site, or genuinely unrouted nets -- inspect "
                "zero_pip_nets.csv before trusting the conflict count if "
                "this number is unexpectedly high relative to total_nets)."
            ),
        },
        "tiles_used_total": len(tile_to_nets),
        "cross_share_switch_box_conflicts": {
            "count": len(conflicts),
            "open_fabric_count": len(open_fabric_conflicts),
            "co_located_terminal_count": len(co_located_conflicts),
            "note": (
                "Each entry is a CANDIDATE coupling-leakage site: a share-0"
                "-only net and a share-1-only net were both routed through "
                "the same tile (switch box). This is a risk indicator per "
                "the worst-case switch-box coupling model (Mueller et al. "
                "2026), NOT a formally verified leak -- no PROLEAD-style "
                "probing-security evaluation has been run. See module "
                "docstring for full scope limitations. "
                "IMPORTANT: 'count' includes BOTH conflict_type values. "
                "'open_fabric_count' is the subset where both nets merely "
                "pass through the shared tile -- these are the genuine "
                "candidate-leak sites the coupling model targets. "
                "'co_located_terminal_count' is the subset where the "
                "shared tile is a physical SOURCE/SINK tile for BOTH nets "
                "(e.g. two share-tagged nets that both terminate at the "
                "same cross-share gadget cell) -- these are not open-fabric "
                "coupling events and cannot be avoided by any routing "
                "strategy, since a cell's own site does not move. Treat "
                "open_fabric_count as the number that matters for routing-"
                "mitigation experiments; co_located_terminal_count reflects "
                "the gadget's own designed cross-share structure."
            ),
        },
    }

    return report, conflicts, tile_to_nets, net_shares, zero_pip_nets


def write_conflicts_csv(conflicts, path="switchbox_conflicts.csv"):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["tile", "share0_net", "share1_net", "conflict_type"]
        )
        writer.writeheader()
        writer.writerows(conflicts)


def write_zero_pip_csv(zero_pip_nets, path="zero_pip_nets.csv"):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["net_name"])
        for n in zero_pip_nets:
            writer.writerow([n])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Milestone 1: cross-share switch-box conflict detection"
    )
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
    report, conflicts, tile_to_nets, net_shares, zero_pip_nets = analyze(args.dcp)

    print(json.dumps(report, indent=2))
    with open("switchbox_conflict_report.json", "w") as f:
        json.dump(report, f, indent=2)

    write_conflicts_csv(conflicts, "switchbox_conflicts.csv")
    write_zero_pip_csv(zero_pip_nets, "zero_pip_nets.csv")

    print(f"\n--- Milestone 1 Result ---")
    print(f"Total nets: {report['net_classification']['total_nets']}")
    print(f"Tiles (switch boxes) used: {report['tiles_used_total']}")
    print(f"Cross-share switch-box conflicts: {report['cross_share_switch_box_conflicts']['count']}")
    print("\nSee switchbox_conflicts.csv for per-conflict detail (inspect before drawing conclusions).")
    print("See zero_pip_nets.csv to sanity-check nets with no recorded PIPs.")
    print("\nConflict entries are RISK INDICATORS, not verified leaks -- see script docstring.")
