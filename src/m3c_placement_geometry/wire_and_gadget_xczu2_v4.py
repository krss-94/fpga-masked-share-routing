"""
Milestone 7: tightly-scoped test of ONE remaining hypothesis from M6.

M6 RESULT (confirmed): open_fabric_count = 2, down from baseline's 3.
Both remaining open_fabric conflicts are INT_X27Y178 / INT_X27Y179 --
both b_sh0_net vs a_sh1_net, both sitting at cross_site_b's own row
(179). The other cross-gadget site (cross_site_a) dropped to ZERO
open_fabric conflicts under the same M6 driver-region logic. So the
asymmetry is real and localized: something about how b_sh0's driver and
a_sh1's driver approach cross_site_b specifically is different from how
a_sh0's driver and b_sh1's driver approach cross_site_a.

HYPOTHESIS THIS SCRIPT TESTS, AND ONLY THIS:
    M6's pick_driver_sites() picked b_sh0's and a_sh1's sites by a fixed
    stride within their respective share-region pools (pool[0],
    pool[len//2]) -- not by anything related to their approach direction
    into cross_site_b. If those two happened to land such that their
    routes converge on the same final-hop corridor into cross_site_b's
    switchbox, that's incidental, not forced -- and choosing sites whose
    approach VECTORS into cross_site_b are more different (ideally
    near-opposite) should let the router take genuinely disjoint final
    hops, removing INT_X27Y178/179 from the conflict list.

WHAT THIS SCRIPT DELIBERATELY DOES NOT CHANGE, to keep this a
single-variable test:
    - cross_site_a / cross_site_b placement logic: IDENTICAL to M5/M6.
    - a_sh0 / b_sh1 driver placement (feeding cross_site_a, already at
      0 open_fabric conflicts in M6): IDENTICAL to M6 -- same pool,
      same stride-pick. No reason to touch a side that's already clean.
    - Everything else: cell creation, INIT, physical pin wiring: verbatim
      from M6/M3b.

ONLY CHANGE: within the SAME share-region pools M6 already used (near
share0 for b_sh0, near share1 for a_sh1 -- this constraint is kept, so
we don't undo M6's fix), search for the (b_sh0_site, a_sh1_site) pair
whose approach-angle to cross_site_b differs the most, instead of M6's
arbitrary pool[0]/pool[len//2] stride-pick.

EXPECTED OUTCOMES, stated honestly before running:
    - If open_fabric drops to 0 or 1: the last-hop corridor was
      incidental to M6's arbitrary site choice, and approach-angle
      separation is a real, usable lever -- worth writing up as a
      concrete mitigation technique.
    - If it holds at 2, possibly at DIFFERENT tiles: cross_site_b's
      switchbox neighborhood has few enough entry points that any two
      approach directions still funnel through overlapping tiles near
      the site -- a local-scale echo of the exact mechanism M1-M4 found
      at the mid-die chokepoint, just confined to a few tiles instead of
      three. That would be a legitimate, separately citable finding:
      the M1-M4 conclusion ("switchbox tiles near a forced convergence
      point are unavoidable") generalizes down to the single-site scale,
      not just the whole-die scale M5 already disproved for the OTHER
      chokepoint.
    - Either result is real evidence. This docstring is written before
      the run specifically so neither outcome gets quietly reframed as
      the other after the fact.

--- Milestone 6 docstring below (still accurate for a_sh0/b_sh1 driver
    placement, which is UNCHANGED in this script) ---

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


def pick_driver_sites(sites_sorted, used_sites, cross_site_b):
    """
    Milestone 7: identical to M6 for a_sh0/b_sh1 (the cross_site_a pair,
    already at 0 open_fabric conflicts -- not touched). For b_sh0/a_sh1
    (the cross_site_b pair, still showing 2 open_fabric conflicts at
    cross_site_b's own row), instead of M6's fixed pool[0]/pool[len//2]
    stride-pick, search the SAME share-region pools for the pair whose
    approach VECTOR into cross_site_b differs the most -- i.e. push them
    toward approaching cross_site_b from different directions, so the
    router isn't funneled into the same final-hop switchbox corridor by
    two nets that happen to enter from a similar angle.

    Returns a dict: driver_name -> site.
    """
    import math

    n = len(sites_sorted)
    used_names = {s.getName() for s in used_sites}

    pool_sh0 = [s for s in sites_sorted[0: n // 12] if s.getName() not in used_names]
    pool_sh1 = [s for s in sites_sorted[-(n // 12):] if s.getName() not in used_names]

    if len(pool_sh0) < 2 or len(pool_sh1) < 2:
        raise RuntimeError(
            f"driver placement pools too small (pool_sh0={len(pool_sh0)}, "
            f"pool_sh1={len(pool_sh1)}) -- widen the n//12 window")

    # a_sh0 / b_sh1 -- UNCHANGED from M6. Feeds cross_site_a, already
    # clean at 0 open_fabric conflicts; no reason to touch it.
    site_a_sh0 = pool_sh0[0]
    site_b_sh1 = pool_sh1[0]

    # b_sh0 / a_sh1 -- the pair feeding cross_site_b. Search for the
    # combination whose approach angle into cross_site_b differs most,
    # within the SAME regional pools M6 used (near-share0 for b_sh0,
    # near-share1 for a_sh1), so we're not undoing the M6 driver-cluster
    # fix -- only refining which specific site within each pool.
    cb_col = cross_site_b.getTile().getColumn()
    cb_row = cross_site_b.getTile().getRow()

    def angle_to_cross_b(site):
        dc = site.getTile().getColumn() - cb_col
        dr = site.getTile().getRow() - cb_row
        return math.atan2(dr, dc)

    def angle_diff(a1, a2):
        d = abs(a1 - a2) % (2 * math.pi)
        return min(d, 2 * math.pi - d)  # 0 = same direction, pi = opposite

    # Skip the sites already claimed by a_sh0/b_sh1 above.
    candidates_sh0 = [s for s in pool_sh0[1:] if s.getName() != site_a_sh0.getName()]
    candidates_sh1 = [s for s in pool_sh1[1:] if s.getName() != site_b_sh1.getName()]

    if not candidates_sh0 or not candidates_sh1:
        raise RuntimeError("not enough remaining candidates for b_sh0/a_sh1 search")

    sample_sh0 = candidates_sh0[::max(1, len(candidates_sh0) // 30)]
    sample_sh1 = candidates_sh1[::max(1, len(candidates_sh1) // 30)]

    best_pair = None
    best_angle_diff = -1
    for cand_b_sh0 in sample_sh0:
        for cand_a_sh1 in sample_sh1:
            ang0 = angle_to_cross_b(cand_b_sh0)
            ang1 = angle_to_cross_b(cand_a_sh1)
            diff = angle_diff(ang0, ang1)
            if diff > best_angle_diff:
                best_angle_diff = diff
                best_pair = (cand_b_sh0, cand_a_sh1)

    site_b_sh0, site_a_sh1 = best_pair

    driver_sites = {
        "u_drv_a_sh0": site_a_sh0,
        "u_drv_a_sh1": site_a_sh1,
        "u_drv_b_sh0": site_b_sh0,
        "u_drv_b_sh1": site_b_sh1,
    }

    for name, site in driver_sites.items():
        print(f"  [Milestone7] {name} -> {site.getName()} "
              f"(col={site.getTile().getColumn()}, row={site.getTile().getRow()})")
    print(f"  [Milestone7] b_sh0/a_sh1 approach-angle separation into "
          f"cross_site_b: {math.degrees(best_angle_diff):.1f} degrees "
          f"(180 = perfectly opposite directions)")

    return driver_sites


def wire_gadget(part_name, out_path):
    from com.xilinx.rapidwright.design import Design, Unisim, DesignTools  # noqa: E402
    from com.xilinx.rapidwright.device import Device, SiteTypeEnum  # noqa: E402
    from com.xilinx.rapidwright.edif import EDIFDirection  # noqa: E402

    print(f"Creating new design on part: {part_name}")
    design = Design("masked_and_gadget_xczu2_v4", part_name)
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
    driver_site_map = pick_driver_sites(sites_sorted, used_sites, cross_site_b)
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
    print("jar (no forbidden-node env var needed), then re-run")
    print("switchbox_conflict_detector.py and compare open_fabric_count")
    print("against the full series so far: baseline (3), M3 (6), M3b (7),")
    print("M4 (3, same tiles as baseline), M5 (4, chokepoint gone but")
    print("driver-cluster + cross-site conflicts appeared), M6 (2, driver")
    print("bug fixed, cross_site_a clean, cross_site_b still showing")
    print("INT_X27Y178/179). THIS run (M7) only changed the b_sh0/a_sh1")
    print("driver sites (angle-optimized against cross_site_b) -- a_sh0/")
    print("b_sh1 are untouched from M6. Check the [Milestone7] angle line")
    print("above, then diff switchbox_conflicts.csv against the M6 run:")
    print("  0-1 open_fabric -> approach-angle separation is a real lever")
    print("  2 open_fabric, SAME tiles (X27Y178/179) -> corridor is forced,")
    print("    angle choice didn't matter")
    print("  2 open_fabric, DIFFERENT tiles -> corridor moved but didn't")
    print("    shrink -- cross_site_b's local neighborhood has few enough")
    print("    entry points that any two directions still overlap somewhere")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", default=os.environ.get("RAPIDWRIGHT_JAR"))
    parser.add_argument("--part", default="xczu2cg-sbva484-1-e")
    parser.add_argument("--out", default="and_gadget_xczu2_v4_wired.dcp")
    args = parser.parse_args()

    if not args.jar:
        print("Error: need --jar or RAPIDWRIGHT_JAR env var")
        sys.exit(1)

    start_rapidwright(args.jar)
    wire_gadget(args.part, args.out)


if __name__ == "__main__":
    main()
