"""
Milestone 5: re-place the two cross-share cells apart from EACH OTHER,
not just apart from their same-share partner.

WHY THIS EXPERIMENT EXISTS:
    M4 (PIP-level hard exclusion in RWRoute.java) forbade the exact 29
    wires the Milestone 1 detector flagged as coupling points. The router
    obeyed -- and landed on the EXACT SAME 5 conflicts (same tiles, same
    nets, same conflict_type split: 3 open_fabric, 2 co_located_terminal),
    just via different sibling wires inside the same switch-boxes. That
    ruled out "wrong wire chosen" as the cause. It pointed instead at
    placement geometry: those tiles (INT_X14Y88/89/90 in the M4 run) are
    apparently the ONLY viable gateway between where share0 and share1
    logic sit -- no routing-side trick can fix a problem that's actually
    about where the cells were placed.

    Looking at the ORIGINAL placement logic (build_and_gadget_xczu2.py /
    wire_and_gadget_xczu2.py, M3/M3b):

        sites_sorted = sorted(all_sites, key=lambda s: s.getTile().getColumn())
        share0_site = sites_sorted[0]                        # leftmost column
        share1_site = sites_sorted[-1]                       # rightmost column
        cross_site_a = sites_sorted[len(sites_sorted)//2 - 1] # \\_ adjacent
        cross_site_b = sites_sorted[len(sites_sorted)//2]     # /  entries

    share0/share1 are already maximally separated (leftmost vs rightmost
    column -- that part was never the problem). But cross_site_a and
    cross_site_b are ADJACENT ENTRIES in a column-sorted list -- i.e.
    essentially the same location, at the exact geometric center. Since
    cross01 needs signals from BOTH share0's side (a_sh0) and share1's
    side (b_sh1), and cross10 needs the mirror (a_sh1, b_sh0), every
    long-haul net on the whole design was funneling toward the same
    few-tile spot in the middle. That's the chokepoint M1 found and M2-M4
    all failed to route around.

    THIS SCRIPT'S CHANGE: pick cross_site_a from roughly the 1/6-1/3
    region of the die (nearer share0) and cross_site_b from roughly the
    2/3-5/6 region (nearer share1), and among candidates in those windows,
    explicitly maximize their column+row separation from each other --
    not just their separation from share0/share1. This is a genuinely
    different placement topology, not a routing-side patch, so it's a
    fair test of whether the M1-M4 chokepoint was a placement artifact.

Everything else (cell creation, INIT setting, driver cells, physical pin
wiring via Net.createPin) is UNCHANGED from the working M3b script --
only pick_placement_sites() and the two lines that call it are new.

USAGE:
    python wire_and_gadget_xczu2_v2.py --jar %RAPIDWRIGHT_JAR% ^
        --part xczu2cg-sbva484-1-e --out and_gadget_xczu2_v2_wired.dcp
"""

import sys
import os
import argparse
import jpype
import jpype.imports


def start_rapidwright(jar_path):
    classpath = jar_path.split(";")
    jpype.startJVM("-Xmx3g", classpath=classpath)


def pick_placement_sites(sites_sorted):
    """
    Milestone 5: spread cross_site_a and cross_site_b apart from EACH
    OTHER (not just from share0/share1), so their two long-haul nets
    don't converge on the same narrow switch-box corridor the way the
    original mid-1/mid adjacent-index placement did.

    share0/share1 keep the original leftmost/rightmost placement -- that
    separation was never the problem, no reason to change it.

    cross_site_a is chosen from a window nearer share0 (1/6 to 1/3 of the
    way across); cross_site_b from the mirrored window nearer share1
    (2/3 to 5/6). Within those windows, we sample candidates and pick the
    pair that maximizes COMBINED column + row distance from each other,
    so they end up in genuinely different regions of the die, not just
    different points along a single sorted axis.
    """
    n = len(sites_sorted)
    share0_site = sites_sorted[0]
    share1_site = sites_sorted[-1]

    window_a = sites_sorted[n // 6: n // 3]
    window_b = sites_sorted[2 * n // 3: 5 * n // 6]

    if not window_a or not window_b:
        raise RuntimeError(
            f"placement windows came up empty (n={n}, "
            f"window_a={len(window_a)}, window_b={len(window_b)}) -- "
            f"device may have far fewer SLICEL sites than expected, "
            f"inspect all_sites count before continuing")

    def row_of(site):
        return site.getTile().getRow()

    def col_of(site):
        return site.getTile().getColumn()

    # Sample rather than brute-force every pair -- a device can have
    # thousands of SLICEL sites, and we only need a good pair, not the
    # optimal one.
    sample_a = window_a[::max(1, len(window_a) // 40)]
    sample_b = window_b[::max(1, len(window_b) // 40)]

    best_pair = None
    best_distance = -1
    for site_a in sample_a:
        for site_b in sample_b:
            col_dist = abs(col_of(site_a) - col_of(site_b))
            row_dist = abs(row_of(site_a) - row_of(site_b))
            combined = col_dist + row_dist
            if combined > best_distance:
                best_distance = combined
                best_pair = (site_a, site_b)

    cross_site_a, cross_site_b = best_pair
    print(f"  [Milestone5] cross_site_a={cross_site_a.getName()} "
          f"(col={col_of(cross_site_a)}, row={row_of(cross_site_a)})")
    print(f"  [Milestone5] cross_site_b={cross_site_b.getName()} "
          f"(col={col_of(cross_site_b)}, row={row_of(cross_site_b)})")
    print(f"  [Milestone5] separation from each other: "
          f"col_dist={abs(col_of(cross_site_a) - col_of(cross_site_b))}, "
          f"row_dist={abs(row_of(cross_site_a) - row_of(cross_site_b))} "
          f"(original M3/M3b placement had these adjacent, i.e. ~0 separation)")

    return share0_site, share1_site, cross_site_a, cross_site_b


def wire_gadget(part_name, out_path):
    from com.xilinx.rapidwright.design import Design, Unisim, DesignTools  # noqa: E402
    from com.xilinx.rapidwright.device import Device, SiteTypeEnum  # noqa: E402
    from com.xilinx.rapidwright.edif import EDIFDirection  # noqa: E402

    print(f"Creating new design on part: {part_name}")
    design = Design("masked_and_gadget_xczu2_v2", part_name)
    device = design.getDevice()
    print(f"Device loaded: {device.getName()}, {device.getAllTiles().size()} tiles")

    print("\nQuerying available SLICE sites for placement...")
    all_sites_raw = device.getAllSites()
    all_sites = [s for s in all_sites_raw if s.getSiteTypeEnum() == SiteTypeEnum.SLICEL]
    print(f"  Found {len(all_sites)} SLICEL sites (out of {len(all_sites_raw)} total sites)")

    if len(all_sites) < 4:
        print("ERROR: not enough SLICEL sites found -- device query may be wrong")
        sys.exit(1)

    sites_sorted = sorted(all_sites, key=lambda s: s.getTile().getColumn())

    print("\nPicking placement sites (Milestone 5: cross cells spread apart)...")
    share0_site, share1_site, cross_site_a, cross_site_b = pick_placement_sites(sites_sorted)

    # (site, bel, input0_signal, input1_signal)
    placement_spec = {
        "u_and_sh0":     (share0_site,  "A6LUT", "a_sh0", "b_sh0"),
        "u_and_sh1":     (share1_site,  "A6LUT", "a_sh1", "b_sh1"),
        "u_and_cross01": (cross_site_a, "A6LUT", "a_sh0", "b_sh1"),
        "u_and_cross10": (cross_site_b, "A6LUT", "a_sh1", "b_sh0"),
    }

    print("\nCreating and placing cells...")
    cells = {}
    for name, (site, bel, in0, in1) in placement_spec.items():
        placement_str = f"{site.getName()}/{bel}"
        try:
            cell = design.createAndPlaceCell(name, Unisim.LUT2, placement_str)
        except Exception as e:
            print(f"  FAILED to place {name}: {e}")
            sys.exit(1)
        cells[name] = cell
        print(f"  Placed {name} at {placement_str} "
              f"(tile column {site.getTile().getColumn()})")

    print("\nSetting LUT INIT (AND on I0,I1) for all 4 cells...")
    for name, cell in cells.items():
        try:
            cell.addProperty("INIT", "4'h8")
        except Exception as e:
            print(f"  FAILED to set INIT on {name}: {e}")
            sys.exit(1)
        print(f"  {name}.INIT = 4'h8")

    print("\nCreating 4 driver cells (LUT1, constant output) to act as ")
    print("real signal sources for a0/a1/b0/b1 -- VCC/GND nets don't work ")
    print("here: they resolve via local site tie-off and never touch ")
    print("general routing, so RWRoute saw 0 connections last run. A ")
    print("placed LUT1 with a constant INIT gives a real O-pin source ")
    print("that must actually route across the die, same as the original ")
    print("design's IBUF-driven a/b signals.")
    driver_sites = sites_sorted[100:104]  # arbitrary, away from the 4 already used
    driver_names = ["u_drv_a_sh0", "u_drv_a_sh1", "u_drv_b_sh0", "u_drv_b_sh1"]
    drivers = {}
    for i, dname in enumerate(driver_names):
        site = driver_sites[i]
        placement_str = f"{site.getName()}/A6LUT"
        drv = design.createAndPlaceCell(dname, Unisim.LUT1, placement_str)
        drv.addProperty("INIT", "2'h3")  # constant-1 output regardless of I0
        drivers[dname] = drv
        print(f"  Placed {dname} at {placement_str} (constant driver)")

    input_names = ["a_sh0", "a_sh1", "b_sh0", "b_sh1"]
    input_driver = {
        "a_sh0": "u_drv_a_sh0", "a_sh1": "u_drv_a_sh1",
        "b_sh0": "u_drv_b_sh0", "b_sh1": "u_drv_b_sh1",
    }

    print("\nCreating input nets (driven by the LUT1 constant cells)...")
    input_fanout = {name: [] for name in input_names}
    for cell_name, (_, _, in0, in1) in placement_spec.items():
        input_fanout[in0].append((cell_name, "I0"))
        input_fanout[in1].append((cell_name, "I1"))

    def add_physical_pin(net, cell, logical_pin):
        """Resolve a cell's logical pin to its physical site pin and attach
        it to the net as a real SitePinInst. Net.createPin(String, SiteInst)
        is the actual physical-layer API (confirmed working in M3b)."""
        site_pin_name = cell.getCorrespondingSitePinName(logical_pin)
        if site_pin_name is None:
            raise RuntimeError(
                f"getCorrespondingSitePinName returned None for "
                f"{cell.getName()}.{logical_pin} -- pin may not map "
                f"directly to a site pin (routethru?) or BEL/site type ")
        net.createPin(site_pin_name, cell.getSiteInst())

    for pname, sinks in input_fanout.items():
        net = design.createNet(pname + "_net")
        # logical (EDIF) wiring -- kept for a consistent netlist on disk
        logical_net = net.getLogicalNet()
        driver_cell = drivers[input_driver[pname]]
        logical_net.createPortInst("O", driver_cell)
        for cell_name, pin in sinks:
            logical_net.createPortInst(pin, cells[cell_name])
        # physical wiring -- this is what RWRoute actually routes
        try:
            add_physical_pin(net, driver_cell, "O")
            for cell_name, pin in sinks:
                add_physical_pin(net, cells[cell_name], pin)
        except Exception as e:
            print(f"  FAILED physical pin creation on {pname}_net: {e}")
            sys.exit(1)
        print(f"  {pname}_net: {input_driver[pname]}.O -> "
              f"{', '.join(f'{c}.{p}' for c, p in sinks)} "
              f"({len(net.getPins())} physical pins)")

    print("\nOutputs left unconnected -- not needed for the routing-")
    print("geometry study, and would need OBUF/IOB placement same as ")
    print("inputs would have.")

    print(f"\nWriting checkpoint: {out_path}")
    design.writeCheckpoint(out_path)
    print("Done.")
    print("\nNext step: route it with the UNPATCHED standalone RapidWright")
    print("jar (no forbidden-node env var needed -- this experiment tests")
    print("placement, not routing constraints), then re-run")
    print("switchbox_conflict_detector.py and compare open_fabric_count")
    print("against baseline (3), M3 soft-penalty (6), M3b hard-exclusion (7),")
    print("and M4 node-level exclusion (3, same tiles as baseline).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", default=os.environ.get("RAPIDWRIGHT_JAR"))
    parser.add_argument("--part", default="xczu2cg-sbva484-1-e")
    parser.add_argument("--out", default="and_gadget_xczu2_v2_wired.dcp")
    args = parser.parse_args()

    if not args.jar:
        print("Error: need --jar or RAPIDWRIGHT_JAR env var")
        sys.exit(1)

    start_rapidwright(args.jar)
    wire_gadget(args.part, args.out)


if __name__ == "__main__":
    main()
