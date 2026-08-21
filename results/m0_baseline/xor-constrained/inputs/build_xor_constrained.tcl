# build_xor_constrained.tcl
# Re-runs the XOR gadget (gadget #2) WITH share_separation.xdc applied,
# for direct comparison against the unconstrained baseline
# (experiments/0002-xor-gadget/outputs/).
#
# Usage:
#   vivado -mode batch -source build_xor_constrained.tcl

set part_name xc7a100tcsg324-1
set top_module masked_xor_gadget
set rtl_file masked_xor_gadget.v
set constraint_file share_separation.xdc

read_verilog $rtl_file
read_xdc $constraint_file

synth_design -top $top_module -part $part_name

write_checkpoint -force synth_xor_constrained.dcp
report_utilization -file synth_utilization_xor_constrained.rpt

opt_design
place_design
route_design

write_checkpoint -force placed_routed_xor_constrained.dcp
write_edf -force placed_routed_xor_constrained.edf

report_utilization -file impl_utilization_xor_constrained.rpt
report_route_status -file route_status_xor_constrained.rpt
report_drc -file post_route_drc_xor_constrained.rpt
report_timing_summary -file post_route_timing_summary_xor_constrained.rpt

puts "XOR constrained build complete: placed_routed_xor_constrained.dcp and reports written."
