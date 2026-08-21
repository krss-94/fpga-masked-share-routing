# build_and_soft.tcl
# Re-runs the AND gadget with share_separation_soft.xdc (IS_SOFT pblocks,
# no CONTAIN_ROUTING) instead of the hard constraint that failed routing.
#
# Usage:
#   vivado -mode batch -source build_and_soft.tcl

set part_name xc7a100tcsg324-1
set top_module masked_and_gadget
set rtl_file masked_and_gadget.v
set constraint_file share_separation_soft.xdc

read_verilog $rtl_file
read_xdc $constraint_file

synth_design -top $top_module -part $part_name

write_checkpoint -force synth_and_soft.dcp
report_utilization -file synth_utilization_and_soft.rpt

opt_design
place_design
route_design

write_checkpoint -force placed_routed_and_soft.dcp
write_edf -force placed_routed_and_soft.edf

report_utilization -file impl_utilization_and_soft.rpt
report_route_status -file route_status_and_soft.rpt
report_drc -file post_route_drc_and_soft.rpt
report_timing_summary -file post_route_timing_summary_and_soft.rpt

puts "AND soft-constrained build complete: placed_routed_and_soft.dcp and reports written."
