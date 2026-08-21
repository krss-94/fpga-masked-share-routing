"""
Milestone 3b: wire the masked AND gadget's LUT logic + nets on xczu2cg.

Follows on from build_and_gadget_xczu2.py, which placed 4 empty LUT2 sites
with no INIT and no nets. This script rebuilds the design (same placement
logic) and adds:

  1. INIT="4'h8" on all 4 LUT2s -- they're all just an AND of I0,I1. What
     differs between them is which top-level signal feeds which pin:
         u_and_sh0:     I0=a0, I1=b0   (share 0, "clean" term)
         u_and_sh1:     I0=a1, I1=b1   (share 1, "clean" term)
         u_and_cross01: I0=a0, I1=b1   (cross term)
         u_and_cross10: I0=a1, I1=b0   (cross term)
     Note the fanout: a0 -> {sh0, cross01}, b1 -> {sh1, cross01},
     a1 -> {sh1, cross10}, b0 -> {sh0, cross10}. Those shared source nets
     are what force routing between the far-apart share sites and the
     mid-device cross sites -- that's the actual thing worth measuring
     once this routes.
  2. Top-level ports a0,a1,b0,b1 (in) and sh0,sh1,cross01,cross10 (out),
     wired directly to the logical netlist (no IBUF/OBUF -- this is a
     placement/routing-geometry study checkpoint, not a bitstream target,
     so we skip pad buffering deliberately).
  3. Nets connecting each port to its LUT pin(s).

HONEST RISK NOTE: the EDIFNet.createPortInst(...) overloads and the
Cell -> EDIFCellInst plumbing below are written from general RapidWright
API structure, NOT re-verified against your exact JAR. Two likely failure
points if this breaks:
  - `net.getLogicalNet()` may not exist on this version; you may need to
    go through `design.getNetlist()` / `EDIFNetlist.getTopCell()` more
    directly, or create the EDIFNet yourself before calling
    `design.createNet()`.
  - `EDIFNet.createPortInst(String, Cell)` may not accept a `Cell`
    directly -- if not, swap to `cell.getEDIFCellInst()` explicitly.
Paste back whatever error comes up, same drill as last time.

USAGE:
    python wire_and_gadget_xczu2.py --jar %RAPIDWRIGHT_JAR% \\
        --part xczu2cg-sbva484-1-e --out and_gadget_xczu2_wired.dcp
"""

import sys
import os
import argparse
import jpype
import jpype.imports


def start_rapidwright(jar_path):
    jpype.startJVM("-Xmx3g", classpath=[jar_path])


def wire_gadget(part_name, out_path):
    from com.xilinx.rapidwright.design import Design, Unisim, DesignTools  # noqa: E402
    from com.xilinx.rapidwright.device import Device, SiteTypeEnum  # noqa: E402
    from com.xilinx.rapidwright.edif import EDIFDirection  # noqa: E402

    print(f"Creating new design on part: {part_name}")
    design = Design("masked_and_gadget_xczu2", part_name)
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
    share0_site = sites_sorted[0]
    share1_site = sites_sorted[-1]
    cross_site_a = sites_sorted[len(sites_sorted) // 2 - 1]
    cross_site_b = sites_sorted[len(sites_sorted) // 2]

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
        it to the net as a real SitePinInst. This is the piece
        createMissingSitePinInsts turned out NOT to do (confirmed: 0 pins
        after calling it) -- Net.createPin(String siteJPinName, SiteInst)
        is the actual physical-layer API, per the overload list Java gave
        us earlier."""
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
    print("\nNext step after this loads cleanly: route it (RWRoute -- confirm")
    print("it doesn't hit the same Series7 refusal you hit on the Artix-7")
    print("part; UltraScale+ should be supported) and re-run the")
    print("switchbox_conflict_detector.py from Milestone 1 against the")
    print("wired+routed checkpoint.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", default=os.environ.get("RAPIDWRIGHT_JAR"))
    parser.add_argument("--part", default="xczu2cg-sbva484-1-e")
    parser.add_argument("--out", default="and_gadget_xczu2_wired.dcp")
    args = parser.parse_args()

    if not args.jar:
        print("Error: need --jar or RAPIDWRIGHT_JAR env var")
        sys.exit(1)

    start_rapidwright(args.jar)
    wire_gadget(args.part, args.out)


if __name__ == "__main__":
    main()
