# build_nand_constrained.tcl
# Re-runs the NAND gadget (gadget #3) WITH the share_separation.xdc
# placement constraint applied, for direct comparison against the
# unconstrained baseline (experiments/0003-nand-gadget/outputs/).
#
# This is the self-initiated follow-up experiment described in
# share_separation.xdc's header comment -- testing one candidate
# mitigation against the distance indicator, beyond the frozen scope.
#
# Usage:
#   vivado -mode batch -source build_nand_constrained.tcl

set part_name xc7a100tcsg324-1
set top_module masked_nand_gadget
set rtl_file masked_nand_gadget.v
set constraint_file share_separation.xdc

# --- Read design + constraints ---
read_verilog $rtl_file
read_xdc $constraint_file

# --- Synthesis ---
synth_design -top $top_module -part $part_name

write_checkpoint -force synth_constrained.dcp
report_utilization -file synth_utilization_constrained.rpt

# --- Implementation: opt, place, route ---
opt_design
place_design
route_design

write_checkpoint -force placed_routed_constrained.dcp
write_edf -force placed_routed_constrained.edf

report_utilization -file impl_utilization_constrained.rpt
report_route_status -file route_status_constrained.rpt
report_drc -file post_route_drc_constrained.rpt
report_timing_summary -file post_route_timing_summary_constrained.rpt

puts "Constrained build complete: placed_routed_constrained.dcp and reports written."
