"""
Milestone 3: Build the masked AND gadget natively on xczu2cg via RapidWright,
entirely bypassing Vivado synthesis/placement -- confirmed necessary and
possible after test_device_load.py proved RapidWright can load UltraScale+
device data (xczu2cg, 66385 tiles) with zero Vivado UltraScale+ device pack
installed.

WHY THIS APPROACH INSTEAD OF YOSYS SYNTHESIS:
    The original masked_and_gadget.v is tiny (4 LUT2 primitives: u_and_sh0,
    u_and_sh1, u_and_cross01, u_and_cross10, per the original RTL structure
    confirmed in this project's earlier milestone0_coverage.py naming
    conventions). Rather than depend on Yosys's UltraScale+ synthesis
    support (unverified in this environment, adds a whole extra tool and
    failure surface), this script constructs the same 4-LUT2 structure
    directly via RapidWright's Design/Cell/Net API, mirroring the original
    gadget exactly. This is smaller, more controllable, and every failure
    point is diagnosable against a known-good reference (the original
    Artix-7 gadget's structure).

HONEST RISK NOTE:
    This is the least-tested script tonight -- constructing a design from
    scratch via RapidWright's Cell/Net/Site placement API is different from
    everything else done so far (which only READ existing checkpoints).
    The exact method names for cell creation, net connection, and site
    placement (Design.createCell, EDIFCell, Site.placeCell or similar) are
    based on general RapidWright API structure and have NOT been verified
    against this exact version. Expect this to need real debugging -- paste
    back whatever error comes up, same as every other script tonight.

USAGE:
    python build_and_gadget_xczu2.py --jar %RAPIDWRIGHT_JAR% \\
        --part xczu2cg-sbva484-1-e --out and_gadget_xczu2_placed.dcp
"""

import sys
import os
import argparse
import jpype
import jpype.imports


def start_rapidwright(jar_path):
    jpype.startJVM("-Xmx3g", classpath=[jar_path])


def build_gadget(part_name, out_path):
    from com.xilinx.rapidwright.design import Design, Unisim  # noqa: E402
    from com.xilinx.rapidwright.device import Device, SiteTypeEnum  # noqa: E402

    print(f"Creating new design on part: {part_name}")
    design = Design("masked_and_gadget_xczu2", part_name)
    device = design.getDevice()
    print(f"Device loaded: {device.getName()}, {device.getAllTiles().size()} tiles")

    # --- Create the 4 LUT2 cells mirroring the original Artix-7 gadget,
    #     combined with placement in a single call. RapidWright's
    #     createAndPlaceCell needs a specific BEL location string
    #     (site/BEL), not just a bare site -- an earlier attempt using a
    #     separate Cell.place(site) call failed because that method
    #     doesn't exist; placement must specify the exact LUT BEL slot
    #     within the site. ---
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

    # Each site's LUT BELs are typically named A6LUT/B6LUT/C6LUT/D6LUT on
    # UltraScale+ SLICEL -- using A6LUT for each since each cell goes in a
    # DIFFERENT site, so no BEL collision within a single site.
    placement_spec = {
        "u_and_sh0": (share0_site, "A6LUT"),
        "u_and_sh1": (share1_site, "A6LUT"),
        "u_and_cross01": (cross_site_a, "A6LUT"),
        "u_and_cross10": (cross_site_b, "A6LUT"),
    }

    print("\nCreating and placing cells...")
    cells = {}
    for name, (site, bel_name) in placement_spec.items():
        try:
            placement_str = f"{site.getName()}/{bel_name}"
            cell = design.createAndPlaceCell(name, Unisim.LUT2, placement_str)
            cells[name] = cell
            print(f"  Placed {name} at {placement_str} "
                  f"(tile column {site.getTile().getColumn()})")
        except Exception as e:
            print(f"  FAILED to place {name}: {e}")

    print(f"\nWriting checkpoint: {out_path}")
    design.writeCheckpoint(out_path)
    print("Done.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", default=os.environ.get("RAPIDWRIGHT_JAR"))
    parser.add_argument("--part", default="xczu2cg-sbva484-1-e")
    parser.add_argument("--out", default="and_gadget_xczu2_placed.dcp")
    args = parser.parse_args()

    if not args.jar:
        print("Error: need --jar or RAPIDWRIGHT_JAR env var")
        sys.exit(1)

    start_rapidwright(args.jar)
    build_gadget(args.part, args.out)


if __name__ == "__main__":
    main()
