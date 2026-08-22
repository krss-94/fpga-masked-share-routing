set PART        "xc7a100tcsg324-1"
set OUTDIR      "./test3_place_route_separated_out"
set SYNTH_CKPT  "../test2_synth_out/post_synth.dcp"
set XDC_FILE    "../share_separation.xdc"
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

proc get_cell_xy {cell_name} {
    set c [get_cells -quiet -hierarchical -filter "NAME =~ *${cell_name}*"]
    if {[llength $c] == 0} { return "" }
    set c [lindex $c 0]
    set loc [get_property -quiet LOC $c]
    if {$loc == ""} { return "" }
    if {[regexp {X(\d+)Y(\d+)} $loc -> x y]} {
        return [list $x $y $loc $c]
    }
    return ""
}

set share_pairs {
    {a_sh0_r a_sh1_r}
    {b_sh0_r b_sh1_r}
    {t0_sh0_reg t0_sh1_reg}
    {q_sh0_reg  q_sh1_reg}
}

set fh [open "$OUTDIR/physical_separation.rpt" w]
puts $fh "pair_share0,pair_share1,loc_share0,loc_share1,manhattan_distance_tiles"
foreach pair $share_pairs {
    set n0 [lindex $pair 0]
    set n1 [lindex $pair 1]
    set r0 [get_cell_xy $n0]
    set r1 [get_cell_xy $n1]
    if {$r0 == "" || $r1 == ""} {
        puts $fh "${n0},${n1},NOT_FOUND_OR_UNPLACED,NOT_FOUND_OR_UNPLACED,NA"
        continue
    }
    set x0 [lindex $r0 0]; set y0 [lindex $r0 1]; set loc0 [lindex $r0 2]
    set x1 [lindex $r1 0]; set y1 [lindex $r1 1]; set loc1 [lindex $r1 2]
    set dist [expr {abs($x1-$x0) + abs($y1-$y0)}]
    puts $fh "${n0},${n1},${loc0},${loc1},${dist}"
    if {$dist <= 1} {
        puts "WARNING: '$n0' and '$n1' are placed within $dist tile(s) of each other ($loc0 vs $loc1) -- minimal physical separation between shares."
    }
}
close $fh

proc get_net_nodes {net_pattern} {
    set nets [get_nets -quiet -hierarchical -filter "NAME =~ *${net_pattern}*"]
    set all_nodes {}
    foreach n $nets {
        set nodes [get_nodes -quiet -of_objects $n]
        foreach nd $nodes {
            set tile [get_property -quiet TILE $nd]
            if {$tile != ""} { lappend all_nodes $tile }
        }
    }
    return $all_nodes
}

set net_pairs {
    {a_sh0_r a_sh1_r}
    {b_sh0_r b_sh1_r}
    {t0_sh0_reg t0_sh1_reg}
    {q_sh0_reg  q_sh1_reg}
    {term_sh0 term_sh1}
}

set fh [open "$OUTDIR/shared_routing_resources.rpt" w]
puts $fh "net_share0,net_share1,shared_tile_count,shared_tiles"
foreach pair $net_pairs {
    set n0 [lindex $pair 0]
    set n1 [lindex $pair 1]
    set tiles0 [get_net_nodes $n0]
    set tiles1 [get_net_nodes $n1]
    set shared {}
    foreach t $tiles0 {
        if {[lsearch -exact $tiles1 $t] >= 0 && [lsearch -exact $shared $t] < 0} {
            lappend shared $t
        }
    }
    set count [llength $shared]
    puts $fh "${n0},${n1},${count},[join $shared { }]"
    if {$count > 0} {
        puts "WARNING: nets matching '$n0' and '$n1' share $count physical tile(s): $shared -- potential routing-resource overlap between shares."
    }
}
close $fh

set watch_cells {a_sh0_r a_sh1_r b_sh0_r b_sh1_r t0_sh0_reg t0_sh1_reg q_sh0_reg q_sh1_reg}

set fh [open "$OUTDIR/site_sharing_summary.rpt" w]
puts $fh "site,occupants"
array set site_members {}
foreach pat $watch_cells {
    set cells [get_cells -quiet -hierarchical -filter "NAME =~ *${pat}*"]
    foreach c $cells {
        set site [get_property -quiet SITE $c]
        set bel  [get_property -quiet BEL $c]
        if {$site != ""} {
            lappend site_members($site) "$pat:$c:$bel"
        }
    }
}
foreach site [array names site_members] {
    set members $site_members($site)
    puts $fh "${site},[join $members {  |  }]"
    if {[llength $members] > 1} {
        puts "NOTE: SITE $site hosts multiple watched cells: $members"
    }
}
close $fh

puts "TEST 3 (share-separated) place/route complete. Outputs in $OUTDIR"
puts "Check physical_separation.rpt, shared_routing_resources.rpt, and site_sharing_summary.rpt."
