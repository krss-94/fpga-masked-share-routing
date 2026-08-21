# mitigate_switchbox_conflicts.tcl
#
# Milestone 2: targeted rip-up/re-route mitigation, driven by Milestone 1's
# switch_box_conflict_detector.py output (switchbox_conflicts.csv).
#
# WHAT THIS DOES: reads the list of nets flagged as sharing a tile (switch
# box or CLB) with a different-share net, unroutes ONLY those specific
# nets, and re-routes them, leaving everything else fixed in place. This
# is the automated analogue of what Mueller et al. 2026 did manually --
# identify a specific conflicting net, unroute it, reroute it, re-verify.
#
# WHAT THIS DOES NOT DO / HONEST LIMITATIONS:
#   - Vivado has no scriptable "avoid this exact tile" routing directive.
#     There is no EXCLUDE_ROUTING pblock property (confirmed against AMD
#     UG912 documentation) and no per-net "prohibited tile" mechanism
#     exposed via Tcl for arbitrary routing resources. This script cannot
#     GUARANTEE the re-route avoids the same tile -- Vivado's router may
#     legitimately put the net back through the exact same switch box,
#     since nothing has changed about resource availability or cost.
#   - This is an experimental first attempt, not a proven mitigation
#     technique. Its actual effectiveness must be measured by re-running
#     switch_box_conflict_detector.py (Milestone 1) against the new
#     checkpoint afterward -- if the conflict count did not drop, this
#     approach needs to be revised (e.g. unrouting BOTH nets in a
#     conflicting pair together, so the router must resolve them jointly
#     instead of one at a time; or iterating this script multiple times,
#     since Vivado's router has some run-to-run variation).
#   - This script only unroutes/reroutes the specific nets found in
#     switchbox_conflicts.csv from the LAST Milestone 1 run. If you change
#     the design between runs, regenerate that CSV first.
#
# USAGE (from Vivado's Tcl Console, with the checkpoint already open):
#   source mitigate_switchbox_conflicts.tcl
#
# Expects switchbox_conflicts.csv to be in the current working directory
# (same folder milestone0_coverage.py / switchbox_conflict_detector.py
# already write their output to).

set conflicts_csv "switchbox_conflicts.csv"

if {![file exists $conflicts_csv]} {
    puts "ERROR: $conflicts_csv not found in current directory."
    puts "Run switchbox_conflict_detector.py first, and run this script"
    puts "from the same directory that CSV was written to."
    return
}

# --- Parse the CSV to get the unique set of conflicting net names ---
# CSV columns: tile,share0_net,share1_net
set fp [open $conflicts_csv r]
set lines [split [read $fp] "\n"]
close $fp

set net_set [dict create]
set line_count 0
foreach line $lines {
    incr line_count
    if {$line_count == 1} {
        continue
    }
    set line [string trim $line]
    if {$line eq ""} {
        continue
    }
    set fields [split $line ","]
    if {[llength $fields] < 3} {
        continue
    }
    set share0_net [lindex $fields 1]
    set share1_net [lindex $fields 2]
    dict set net_set $share0_net 1
    dict set net_set $share1_net 1
}

set unique_nets [dict keys $net_set]
set n_nets [llength $unique_nets]

puts "=============================================================="
puts "Milestone 2: targeted rip-up/re-route mitigation"
puts "=============================================================="
puts "Parsed $conflicts_csv: found $n_nets unique conflicting net names."

if {$n_nets == 0} {
    puts "No conflicting nets found -- nothing to mitigate. Exiting."
    return
}

# --- Resolve net names to actual net objects, warn on any that don't match ---
set nets_to_reroute {}
set unresolved_nets {}
foreach net_name $unique_nets {
    set matched [get_nets -quiet $net_name]
    if {$matched eq ""} {
        lappend unresolved_nets $net_name
    } else {
        lappend nets_to_reroute $matched
    }
}

if {[llength $unresolved_nets] > 0} {
    puts "\nWARNING: the following net names from the CSV did not resolve"
    puts "to an actual net in the currently open design. This can happen"
    puts "if the CSV is stale (from a different checkpoint) or if net"
    puts "names contain characters Tcl needs escaped (e.g. '/' in"
    puts "hierarchical names like u_and_sh1/y). Inspect these manually"
    puts "before trusting the mitigation result:"
    foreach n $unresolved_nets {
        puts "  - $n"
    }
}

puts "\nResolved [llength $nets_to_reroute] of $n_nets nets. Proceeding"
puts "with unroute + reroute on the resolved set only."

# --- Unroute only the flagged nets (leaves everything else fixed) ---
puts "\nUnrouting flagged nets..."
route_design -unroute -nets $nets_to_reroute

# --- Reroute only those nets ---
puts "Re-routing flagged nets..."
route_design -nets $nets_to_reroute

# --- Report status before/after so the result is visible immediately ---
puts "\n--- Post-mitigation route status ---"
report_route_status

# --- Write a new checkpoint, distinct name so Milestone 0/1 results
#     are never silently overwritten ---
set out_dcp "placed_routed_and_mitigated.dcp"
write_checkpoint -force $out_dcp
puts "\nWrote $out_dcp."
puts "\nNEXT STEP (do this outside Vivado, in your Python/RapidWright"
puts "environment): re-run switch_box_conflict_detector.py against"
puts "$out_dcp and compare the conflict count to the previous run."
puts "This script's own success or failure is NOT determined by whether"
puts "route_design reported errors -- it is determined by whether the"
puts "conflict count actually dropped. A clean route_design result here"
puts "only means Vivado found SOME legal routing, not that it avoided"
puts "the same switch box."
