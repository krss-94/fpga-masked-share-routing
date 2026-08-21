# ============================================================================
# Milestone 0 build script: RTL -> synthesized+implemented DCP
#
# Run with: vivado -mode batch -source build_milestone0.tcl
# Target part is a placeholder Artix-7 device to match the benchmark
# family used elsewhere in this project (TCHES masked Kyber/Dilithium/
# Saber reference designs) -- swap -part if targeting a different device.
# ============================================================================

set part xc7a100tcsg324-1
set top  masked_and_gadget

read_verilog -sv [glob ./masked_and_gadget.v]

# Out-of-context synthesis: this is a standalone gadget, not a full
# top-level design with IOBUFs -- keeps the test artifact minimal,
# consistent with "smallest possible benchmark" per the plan.
synth_design -top $top -part $part -mode out_of_context \
    -flatten_hierarchy none

# Explicit report before optimization/implementation, as a baseline
# to compare against post-P&R cell count. A large discrepancy here
# vs. post-route is itself a Milestone 0 data point (were dont_touch
# cells actually respected?).
report_utilization -file synth_utilization.rpt

write_checkpoint -force synth.dcp

opt_design
place_design
route_design

report_utilization -file impl_utilization.rpt
report_route_status -file route_status.rpt

# Archived so a future coverage anomaly can be checked against whether
# Vivado silently altered structure to fix a DRC or timing violation,
# rather than re-running the whole flow to find out after the fact.
report_drc -file post_route_drc.rpt
report_timing_summary -file post_route_timing_summary.rpt

# This is the artifact Milestone 0's RapidWright script consumes.
write_checkpoint -force placed_routed.dcp
write_edif -force placed_routed.edf

puts "Milestone 0 build complete: placed_routed.dcp ready for coverage measurement."
