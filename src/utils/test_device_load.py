"""
Standalone device-load test. Does NOT touch Vivado's installed device packs
at all -- this only tests whether RapidWright's own device database (which
appears, based on the successful gnl_test.dcp run, to be independent of
Vivado's local install) can recognize a small UltraScale+ part directly.

If this works, it opens a real possibility: build/place a design via
RapidWright + Yosys entirely outside Vivado, then route with RWRoute --
bypassing the need for a 34GB Vivado UltraScale+ device pack install
altogether.

Usage:
    python test_device_load.py --jar %RAPIDWRIGHT_JAR%
"""
import sys
import os
import argparse
import jpype
import jpype.imports


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", default=os.environ.get("RAPIDWRIGHT_JAR"))
    args = parser.parse_args()

    if not args.jar:
        print("Error: need --jar or RAPIDWRIGHT_JAR env var")
        sys.exit(1)

    jpype.startJVM("-Xmx4g", classpath=[args.jar])

    from com.xilinx.rapidwright.device import Device  # noqa: E402

    # Try a few small UltraScale+ part names directly -- if RapidWright's
    # own device DB has these cached/downloadable independent of Vivado,
    # this succeeds without ever touching Vivado's install.
    candidates = [
        "xczu2cg-sbva484-1-e",   # smallest free-tier Zynq UltraScale+
        "xczu3eg-sbva484-1-e",
        "xcku040-ffva1156-2-e",  # the device used in the gnl_test.dcp example
    ]

    for part in candidates:
        print(f"\nAttempting to load device: {part}")
        try:
            device = Device.getDevice(part)
            if device is None:
                print(f"  -> returned None (not found)")
            else:
                print(f"  -> SUCCESS: loaded {device.getName()}, "
                      f"{device.getAllTiles().size()} tiles")
        except Exception as e:
            print(f"  -> EXCEPTION: {e}")


if __name__ == "__main__":
    main()
