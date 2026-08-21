# build_milestone_nand.tcl
# Synthesis + implementation flow for the masked NAND gadget (gadget #3).
# Mirrors build_milestone0.tcl / build_milestone_xor.tcl structure and
# target part so outputs are directly comparable.
#
# Usage:
#   vivado -mode batch -source build_milestone_nand.tcl

set part_name xc7a100tcsg324-1
set top_module masked_nand_gadget
set rtl_file masked_nand_gadget.v

# --- Read design ---
read_verilog $rtl_file

# --- Synthesis ---
synth_design -top $top_module -part $part_name

write_checkpoint -force synth.dcp
report_utilization -file synth_utilization.rpt

# --- Implementation: opt, place, route ---
opt_design
place_design
route_design

write_checkpoint -force placed_routed.dcp
write_edf -force placed_routed.edf

report_utilization -file impl_utilization.rpt
report_route_status -file route_status.rpt
report_drc -file post_route_drc.rpt
report_timing_summary -file post_route_timing_summary.rpt

puts "Build complete: synth.dcp, placed_routed.dcp, placed_routed.edf, and reports written."
