set part_name xc7a100tcsg324-1
set top_module masked_and_gadget
set rtl_file masked_and_gadget.v
set constraint_file share_separation_placement_only.xdc

read_verilog $rtl_file
read_xdc $constraint_file
synth_design -top $top_module -part $part_name

write_checkpoint -force synth_and_placement_only.dcp
report_utilization -file synth_utilization_and_placement_only.rpt

opt_design
place_design
route_design

report_utilization -file impl_utilization_and_placement_only.rpt
report_route_status -file route_status_and_placement_only.rpt
report_drc -file post_route_drc_and_placement_only.rpt

write_checkpoint -force placed_routed_and_placement_only.dcp
write_edif -force placed_routed_and_placement_only.edf

puts "AND placement-only build complete."