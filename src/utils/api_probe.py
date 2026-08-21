"""
API probe -- run this BEFORE the real cross-tag patch.

Goal: find out how to get the routing-fabric-side TILE that a net's sink
pin actually connects into (the "sink tile" concept RWRoute's own logging
used, e.g. "sink tile: INT_X15Y90"), using whatever your installed
RapidWright jar actually exposes. This is deliberately read-only and
side-effect-free -- it does not write any CSV/JSON, it just prints.

USAGE:
    python api_probe.py and_gadget_xczu2_hardexcl_diag_routed.dcp --jar %RAPIDWRIGHT_JAR%

Paste the FULL output back. Whichever candidate approach succeeds (prints
a real tile name, not an exception) tells us which API to use in the real
patch to switchbox_conflict_detector.py.
"""

import sys
import os
import argparse

import jpype
import jpype.imports


def start_rapidwright(jar_path: str):
    jpype.startJVM(classpath=[jar_path])


def probe(dcp_path: str):
    from com.xilinx.rapidwright.design import Design  # noqa: E402

    print(f"Reading DCP: {dcp_path}")
    design = Design.readCheckpoint(dcp_path)

    # Grab one net we know is share-tagged and has a real sink, from the
    # and_gadget_xczu2 testbed, so results are directly comparable to the
    # RWRoute diagnostic log we already have. Falls back to first non-empty
    # net if the exact name isn't present (e.g. different DCP was passed).
    target_names = ["a_sh0_net", "a_sh1_net", "b_sh0_net", "b_sh1_net"]
    net = None
    for n in design.getNets():
        if str(n.getName()) in target_names:
            net = n
            break
    if net is None:
        print("None of the expected net names found -- falling back to first net with PIPs.")
        for n in design.getNets():
            if len(n.getPIPs()) > 0:
                net = n
                break
    if net is None:
        print("No usable net found at all. Aborting probe.")
        return

    net_name = str(net.getName())
    print(f"\nUsing net: {net_name}")

    # --- Candidate 1: SitePinInst.getConnectedNode().getTile() ---
    print("\n--- Candidate 1: net.getSinkPins() -> pin.getConnectedNode().getTile() ---")
    try:
        sink_pins = net.getSinkPins()
        print(f"  getSinkPins() returned {len(sink_pins)} pin(s)")
        for pin in sink_pins:
            try:
                node = pin.getConnectedNode()
                tile = node.getTile()
                print(f"  pin={pin}  connectedNode={node}  tile={tile.getName()}")
            except Exception as e:
                print(f"  FAILED on this pin: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")

    # --- Candidate 2: SitePinInst.getTile() directly (site/CLB tile, not fabric tile) ---
    print("\n--- Candidate 2: net.getSinkPins() -> pin.getTile() (site tile, for comparison) ---")
    try:
        sink_pins = net.getSinkPins()
        for pin in sink_pins:
            try:
                print(f"  pin={pin}  tile={pin.getTile().getName()}")
            except Exception as e:
                print(f"  FAILED on this pin: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")

    # --- Candidate 3: last PIP in net.getPIPs() nearest the sink ---
    print("\n--- Candidate 3: last entry of net.getPIPs() (approximation, order not guaranteed) ---")
    try:
        pips = net.getPIPs()
        print(f"  getPIPs() returned {len(pips)} PIP(s)")
        if len(pips) > 0:
            last_pip = pips[-1]
            print(f"  last PIP tile: {last_pip.getTile().getName()}")
            first_pip = pips[0]
            print(f"  first PIP tile: {first_pip.getTile().getName()}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")

    # --- Candidate 4: source side, for symmetry ---
    print("\n--- Candidate 4: net.getSource() -> pin.getConnectedNode().getTile() ---")
    try:
        source_pin = net.getSource()
        if source_pin is None:
            print("  getSource() returned None (static-driven net?)")
        else:
            node = source_pin.getConnectedNode()
            print(f"  source pin={source_pin}  tile={node.getTile().getName()}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")

    print("\nDone. Paste this whole block back.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Probe RapidWright API for net sink-tile access")
    parser.add_argument("dcp", help="Path to a routed .dcp")
    parser.add_argument("--jar", default=os.environ.get("RAPIDWRIGHT_JAR"))
    args = parser.parse_args()

    if not args.jar:
        print("Error: --jar or RAPIDWRIGHT_JAR required.")
        sys.exit(1)

    start_rapidwright(args.jar)
    probe(args.dcp)
