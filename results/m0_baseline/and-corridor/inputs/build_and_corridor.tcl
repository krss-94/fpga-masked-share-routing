# build_and_corridor.tcl
# Tests the new quarantined-crossing-corridor constraint
# (share_separation_corridor.xdc) on the AND gadget -- the gadget whose
# genuine cross-share signal broke hard containment entirely.
#
# Usage:
#   vivado -mode batch -source build_and_corridor.tcl

set part_name xc7a100tcsg324-1
set top_module masked_and_gadget
set rtl_file masked_and_gadget.v
set constraint_file share_separation_corridor.xdc

read_verilog $rtl_file
read_xdc $constraint_file

synth_design -top $top_module -part $part_name

write_checkpoint -force synth_and_corridor.dcp
report_utilization -file synth_utilization_and_corridor.rpt

opt_design
place_design
route_design

write_checkpoint -force placed_routed_and_corridor.dcp
write_edf -force placed_routed_and_corridor.edf

report_utilization -file impl_utilization_and_corridor.rpt
report_route_status -file route_status_and_corridor.rpt
report_drc -file post_route_drc_and_corridor.rpt
report_timing_summary -file post_route_timing_summary_and_corridor.rpt

puts "AND corridor-constrained build complete: placed_routed_and_corridor.dcp and reports written."
