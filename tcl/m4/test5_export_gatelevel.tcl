# =====================================================================
# TEST 5 (part 1): Export post-route gate-level netlist + SDF for
# timing simulation. This is the physical implementation of the
# masked_and_gadget -- includes the LUT fracturing and shared control
# set that TEST 4 found. Goal: re-run TEST 1's TVLA methodology
# against THIS netlist to see if physical implementation introduces
# detectable first-order leakage that behavioral sim couldn't show.
# Run in batch mode:
#   vivado -mode batch -source test5_export_gatelevel.tcl
# =====================================================================

set OUTDIR      "./test5_gatelevel_out"
set ROUTE_CKPT  "./test3_place_route_out/post_route.dcp"

file mkdir $OUTDIR

open_checkpoint $ROUTE_CKPT

# ---------------------------------------------------------------------
# 1. Post-route functional+timing netlist for simulation.
#    -mode timesim preserves the physical primitive instances (FDRE,
#    LUT2, LUT4 etc.) with real BEL-level structure, unlike funcsim
#    which can abstract some of it away.
# ---------------------------------------------------------------------
write_verilog -force -mode timesim -sdf_anno true \
    -file "$OUTDIR/masked_and_gadget_timesim.v"

# ---------------------------------------------------------------------
# 2. SDF file with real post-route delays for timing-accurate sim.
# ---------------------------------------------------------------------
write_sdf -force "$OUTDIR/masked_and_gadget_timesim.sdf"

# ---------------------------------------------------------------------
# 3. Dump the exact hierarchical instance paths for every watch
#    signal so the testbench probe list matches reality instead of
#    guessing at post-route naming.
# ---------------------------------------------------------------------
set watch_cells {a_sh0_r a_sh1_r b_sh0_r b_sh1_r t0_sh0 t0_sh1 \
                  u_and_sh0 u_and_sh1 u_and_cross01 u_and_cross10}

set fh [open "$OUTDIR/probe_paths.rpt" w]
puts $fh "watch_signal,hierarchical_cell_path,ref_name"
foreach pat $watch_cells {
    set cells [get_cells -quiet -hierarchical -filter "NAME =~ *${pat}*"]
    foreach c $cells {
        set ref [get_property -quiet REF_NAME $c]
        puts $fh "${pat},${c},${ref}"
    }
}
close $fh

puts "TEST 5 part 1 complete. Outputs in $OUTDIR"
puts "Next: build/adapt testbench using probe_paths.rpt, then run xsim gate-level sim."
