"""
Milestone 6: fix a driver-placement bug found in the M5 result.

WHY THIS EXPERIMENT EXISTS:
    M5 (cross_site_a/cross_site_b spread apart from each other, not just
    from share0/share1) worked exactly as intended for the thing it was
    designed to fix: the M1-M4 mid-die chokepoint at INT_X14-15/Y88-90 is
    COMPLETELY ABSENT from the M5 routed result -- zero tile overlap with
    baseline. That's a real, confirmed causal fix.

    But M5's open_fabric_count went UP (3 -> 4), not down, because two new
    conflicts appeared at INT_X0Y77 and INT_X0Y78 that have nothing to do
    with cross-site placement. Root cause, found by reading M5's own
    driver-placement code:

        driver_sites = sites_sorted[100:104]  # arbitrary, away from the 4 already used

    sites_sorted is sorted by column ONLY. Many SLICEL sites share column
    0 (leftmost), so ties fall back to device enumeration order -- which
    happened to put all 4 drivers at SLICE_X0Y76/77/78/79, one row apart,
    right next to share0_site (SLICE_X0Y179). That's fine for
    u_drv_a_sh0/u_drv_b_sh0 (their consumers are nearby), but
    u_drv_a_sh1 and u_drv_b_sh1 feed signals that need to reach
    share1_site (col 298) and cross_site_b (col 271) -- clear across the
    die. So a share0 net and a share1 net launch from adjacent rows in
    the same local switch-box neighborhood, before either signal goes
    anywhere. That's exactly what the M5 CSV showed: b_sh0_net and
    a_sh1_net conflicting at INT_X0Y77/X0Y78, right at the source.

    This was invisible in M1-M4 because those experiments never touched
    driver placement -- it's a latent bug in "arbitrary, away from the 4
    already used," which never accounted for which SHARE each driver
    belongs to.

    THIS SCRIPT'S CHANGE: keep every M5 fix (cross_site_a/b maximally
    separated from each other) exactly as-is. Only replace the arbitrary
    driver_sites = sites_sorted[100:104] with pick_driver_sites(), which
    places each driver near ITS OWN share's region -- a_sh0/b_sh0 drivers
    near share0_site, a_sh1/b_sh1 drivers near share1_site -- so no
    driver ever has to launch a long-haul net from next to a
    differently-shared driver.

    NOT expected to fix: the other two M5 conflict pairs, INT_X3Y7/X5Y8
    (next to cross_site_a) and INT_X25Y178/X25Y179 (next to cross_site_b).
    Those look structural: u_and_cross01 needs a_sh0 AND b_sh1 to
    physically arrive at the same site, so a share0 net and a share1 net
    converging near that cell's local switchbox isn't a placement mistake
    -- it's what a cross-share gadget inherently is. This run will show
    whether that read is correct: if those 4 conflicts persist unchanged
    while the driver-cluster conflicts disappear, that confirms the
    convergence-at-the-gadget effect is independent of the driver bug.

--- Original Milestone 5 docstring below (still accurate for cross-site
    placement logic, which is UNCHANGED in this script) ---

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


def pick_driver_sites(sites_sorted, used_sites):
    """
    Milestone 6: place each driver near ITS OWN share's region, instead
    of the M5 approach (sites_sorted[100:104], which put all 4 drivers
    adjacent to each other regardless of share -- see module docstring).

    a_sh0/b_sh0 drivers go near share0_site (leftmost column region);
    a_sh1/b_sh1 drivers go near share1_site (rightmost column region).
    Each driver still gets its own distinct site, and none may collide
    with a site already used by share0/share1/cross_site_a/cross_site_b
    (passed in via used_sites).

    Returns a dict: driver_name -> site.
    """
    n = len(sites_sorted)
    used_names = {s.getName() for s in used_sites}

    # Near-share0 pool: leftmost slice, excluding share0_site itself.
    # Near-share1 pool: rightmost slice, excluding share1_site itself.
    pool_sh0 = [s for s in sites_sorted[0: n // 12] if s.getName() not in used_names]
    pool_sh1 = [s for s in sites_sorted[-(n // 12):] if s.getName() not in used_names]

    if len(pool_sh0) < 2 or len(pool_sh1) < 2:
        raise RuntimeError(
            f"driver placement pools too small (pool_sh0={len(pool_sh0)}, "
            f"pool_sh1={len(pool_sh1)}) -- widen the n//12 window")

    # Distinct rows within each pool so the two same-side drivers don't
    # land on top of each other; simple stride-pick, not adjacency-tuned
    # (unlike the cross_site pair, these two never both feed the same
    # cross-gadget cell, so tight adjacency between them isn't the risk
    # -- the risk was adjacency to the OTHER share, which this fixes).
    site_a_sh0 = pool_sh0[0]
    site_b_sh0 = pool_sh0[len(pool_sh0) // 2]
    site_a_sh1 = pool_sh1[0]
    site_b_sh1 = pool_sh1[len(pool_sh1) // 2]

    driver_sites = {
        "u_drv_a_sh0": site_a_sh0,
        "u_drv_a_sh1": site_a_sh1,
        "u_drv_b_sh0": site_b_sh0,
        "u_drv_b_sh1": site_b_sh1,
    }

    for name, site in driver_sites.items():
        print(f"  [Milestone6] {name} -> {site.getName()} "
              f"(col={site.getTile().getColumn()}, row={site.getTile().getRow()})")

    return driver_sites


def wire_gadget(part_name, out_path):
    from com.xilinx.rapidwright.design import Design, Unisim, DesignTools  # noqa: E402
    from com.xilinx.rapidwright.device import Device, SiteTypeEnum  # noqa: E402
    from com.xilinx.rapidwright.edif import EDIFDirection  # noqa: E402

    print(f"Creating new design on part: {part_name}")
    design = Design("masked_and_gadget_xczu2_v3", part_name)
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
    used_sites = [share0_site, share1_site, cross_site_a, cross_site_b]
    driver_site_map = pick_driver_sites(sites_sorted, used_sites)
    driver_names = ["u_drv_a_sh0", "u_drv_a_sh1", "u_drv_b_sh0", "u_drv_b_sh1"]
    drivers = {}
    for dname in driver_names:
        site = driver_site_map[dname]
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
    print("M4 node-level exclusion (3, same tiles as baseline), and")
    print("M5 cross-site separation (4, driver-adjacent + cross-adjacent,")
    print("zero overlap with baseline tiles). This run (M6) should remove")
    print("the driver-cluster conflicts (INT_X0Y77/X0Y78 in M5) while the")
    print("cross-site conflicts (near cross_site_a/cross_site_b) are")
    print("expected to persist -- if they do, that confirms those are")
    print("structural (inherent to the cross-gadget's own convergence),")
    print("not a placement artifact this script can fix.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", default=os.environ.get("RAPIDWRIGHT_JAR"))
    parser.add_argument("--part", default="xczu2cg-sbva484-1-e")
    parser.add_argument("--out", default="and_gadget_xczu2_v3_wired.dcp")
    args = parser.parse_args()

    if not args.jar:
        print("Error: need --jar or RAPIDWRIGHT_JAR env var")
        sys.exit(1)

    start_rapidwright(args.jar)
    wire_gadget(args.part, args.out)


if __name__ == "__main__":
    main()
