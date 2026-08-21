# =====================================================================
# TEST 4: Routing-conflict / physical leakage investigation
# Builds on TEST 3's post_route.dcp. TEST 3 found same/adjacent-slice
# placement but ZERO shared general-fabric routing tiles. That zero
# is expected -- intra-site connections (site pips, LUT fracturing,
# shared control sets) don't appear as routed nodes at all, so TEST 3
# structurally cannot see them. TEST 4 inspects those mechanisms
# directly.
# Run in batch mode:
#   vivado -mode batch -source test4_physical_leakage.tcl
# =====================================================================

set OUTDIR      "./test4_physical_leakage_out"
set ROUTE_CKPT  "./test3_place_route_out/post_route.dcp"

file mkdir $OUTDIR

open_checkpoint $ROUTE_CKPT

set watch_cells {a_sh0_r a_sh1_r b_sh0_r b_sh1_r t0_sh0_reg t0_sh1_reg q_sh0_reg q_sh1_reg}

# ---------------------------------------------------------------------
# 1. BEL-level co-location map: SITE + BEL for every watch cell.
#    Cells sharing a SITE get flagged; cells sharing the same BEL
#    slot pattern (fracturable LUT halves, e.g. A5LUT/A6LUT on the
#    same physical LUT) get flagged harder.
# ---------------------------------------------------------------------
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

# ---------------------------------------------------------------------
# 2. Control set sharing: are any share0/share1 FFs driven by the
#    exact same physical CE/SR/CLK routing (same control set)?
# ---------------------------------------------------------------------
report_control_sets -verbose -file "$OUTDIR/control_sets.rpt"

# ---------------------------------------------------------------------
# 3. Site-internal routing (site pips) for every SITE that hosts a
#    watched cell -- this is the intra-site mechanism TEST 3's
#    tile/node-based check structurally cannot observe.
# ---------------------------------------------------------------------
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

# ---------------------------------------------------------------------
# 4. Cross-reference: for each site hosting >1 watched cell, pull
#    every pin (not just watched ones) mapped into that site, so we
#    can see the full physical neighborhood, including any unrelated
#    logic packed in alongside the shares.
# ---------------------------------------------------------------------
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

puts "TEST 4 physical leakage investigation complete. Outputs in $OUTDIR"
puts "Check site_sharing_summary.rpt, control_sets.rpt, and shared_site_full_contents.rpt first."
