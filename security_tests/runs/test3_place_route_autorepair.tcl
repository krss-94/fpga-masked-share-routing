set PART        "xc7a100tcsg324-1"
set OUTDIR      "./test3_place_route_autorepair_out"
set SYNTH_CKPT  "../test2_synth_out/post_synth.dcp"
set XDC_FILE    "./share_separation_auto_repaired.xdc"
set PLACE_CKPT  "$OUTDIR/post_place.dcp"
set ROUTE_CKPT  "$OUTDIR/post_route.dcp"

file mkdir $OUTDIR

open_checkpoint $SYNTH_CKPT

create_clock -period 10.000 -name clk [get_ports clk]
set_input_delay  -clock clk 2.000 [get_ports {a_sh0 a_sh1 b_sh0 b_sh1 r}]
set_output_delay -clock clk 2.000 [get_ports {q_sh0 q_sh1}]
set_false_path -from [get_ports rst]

read_xdc $XDC_FILE

write_checkpoint -force "$OUTDIR/post_synth_constrained.dcp"

opt_design > "$OUTDIR/opt_design.log"
place_design > "$OUTDIR/place_design.log"
write_checkpoint -force $PLACE_CKPT

route_design > "$OUTDIR/route_design.log"
write_checkpoint -force $ROUTE_CKPT

report_utilization -hierarchical -file "$OUTDIR/utilization_post_route.rpt"
report_timing_summary -file "$OUTDIR/timing_summary_post_route.rpt"
report_route_status -file "$OUTDIR/route_status.rpt"
report_drc -file "$OUTDIR/post_route_drc.rpt"

puts "TEST auto-repair place/route complete. Outputs in $OUTDIR"
