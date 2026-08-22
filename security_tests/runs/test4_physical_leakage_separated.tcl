set OUTDIR      "./test4_physical_leakage_separated_out"
set ROUTE_CKPT  "./test3_place_route_separated_out/post_route.dcp"

file mkdir $OUTDIR

open_checkpoint $ROUTE_CKPT

set watch_cells {a_sh0_r a_sh1_r b_sh0_r b_sh1_r t0_sh0_reg t0_sh1_reg q_sh0_reg q_sh1_reg}

set fh [open "$OUTDIR/bel_colocation_map.rpt" w]
puts $fh "cell_pattern,matched_cell,site,bel"
array set site_members {}
foreach pat $watch_cells {
    set cells [get_cells -quiet -hierarchical -filter "NAME =~ *${pat}*"]
    foreach c $cells {
        set site [get_property -quiet SITE $c]
        set bel  [get_property -quiet BEL $c]
        puts $fh "${pat},${c},${site},${bel}"
        if {$site != ""} {
            lappend site_members($site) "$pat:$c:$bel"
        }
    }
}
close $fh

set fh [open "$OUTDIR/site_sharing_summary.rpt" w]
puts $fh "site,occupants"
foreach site [array names site_members] {
    set members $site_members($site)
    puts $fh "${site},[join $members {  |  }]"
    if {[llength $members] > 1} {
        puts "NOTE: SITE $site hosts multiple watched cells: $members"
    }
}
close $fh

report_control_sets -verbose -file "$OUTDIR/control_sets.rpt"

set fh [open "$OUTDIR/site_pips_used.rpt" w]
puts $fh "site,site_pip,net"
foreach site [array names site_members] {
    set site_obj [get_sites -quiet $site]
    if {$site_obj == ""} { continue }
    set pips [get_site_pips -quiet -of_objects $site_obj -filter {IS_USED}]
    foreach p $pips {
        set net [get_nets -quiet -of_objects $p]
        puts $fh "${site},${p},${net}"
    }
}
close $fh

set fh [open "$OUTDIR/shared_site_full_contents.rpt" w]
foreach site [array names site_members] {
    if {[llength $site_members($site)] <= 1} { continue }
    puts $fh "===== SITE $site ====="
    set site_obj [get_sites -quiet $site]
    set all_cells [get_cells -quiet -of_objects $site_obj]
    foreach c $all_cells {
        set bel [get_property -quiet BEL $c]
        set ref [get_property -quiet REF_NAME $c]
        puts $fh "  cell: $c  bel: $bel  ref_name: $ref"
    }
}
close $fh

puts "TEST 4 (separated) physical leakage investigation complete. Outputs in $OUTDIR"
