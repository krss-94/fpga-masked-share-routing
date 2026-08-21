# =====================================================================
# TEST 2: Synthesis of masked_and_gadget.v
# Device: xc7a100tcsg324-1
# Purpose: OOC synthesis, resource/timing baseline, netlist inspection,
#          check whether term_cross01/term_cross10/t0_sh0/t0_sh1 survive.
# RTL is NOT modified. Run in batch mode:
#   vivado -mode batch -source test2_synth.tcl
# =====================================================================

set PART        "xc7a100tcsg324-1"
set RTL_FILE    "./masked_and_gadget.v"
set TOP         "masked_and_gadget"
set OUTDIR      "./test2_synth_out"
set LOGDIR      "$OUTDIR/logs"

file mkdir $OUTDIR
file mkdir $LOGDIR

set CKPT "$OUTDIR/post_synth.dcp"

if {[file exists $CKPT]} {
    # Reuse prior synthesis result -- avoids re-running synth_design
    # (and its full log) when only downstream reporting changed.
    puts "Found existing checkpoint, opening: $CKPT"
    open_checkpoint $CKPT
} else {
    # -----------------------------------------------------------------
    # 1. Read RTL, no edits
    # -----------------------------------------------------------------
    read_verilog -sv $RTL_FILE

    # -----------------------------------------------------------------
    # 2. Synthesize out-of-context, preserve hierarchy for inspection.
    #    -flatten_hierarchy none keeps module boundaries so we can see
    #    whether the gadget's internal terms still exist as distinct
    #    cells/nets, rather than being merged/optimized into the parent.
    #    No KEEP/DONT_TOUCH attributes are added -- this is the RTL's
    #    natural synthesis behavior, unmodified.
    # -----------------------------------------------------------------
    synth_design -top $TOP -part $PART -mode out_of_context \
        -flatten_hierarchy none \
        -verbose \
        > "$LOGDIR/synth_design.log"

    write_checkpoint -force $CKPT
}

# ---------------------------------------------------------------------
# 3. Utilization report (LUT/FF/IO counts)
# ---------------------------------------------------------------------
report_utilization -hierarchical -file "$OUTDIR/utilization.rpt"

# ---------------------------------------------------------------------
# 4. Timing report (worst slack)
# ---------------------------------------------------------------------
report_timing_summary -file "$OUTDIR/timing_summary.rpt"

# ---------------------------------------------------------------------
# 5. Full netlist hierarchy / cell listing
#    (report_property only accepts one object per call, so loop)
# ---------------------------------------------------------------------
set fh_prop [open "$OUTDIR/cell_properties.rpt" w]
foreach cell [get_cells -hierarchical] {
    puts $fh_prop "===== $cell ====="
    puts $fh_prop [report_property -all -return_string $cell]
}
close $fh_prop

set fh [open "$OUTDIR/netlist_hierarchy.rpt" w]
foreach cell [get_cells -hierarchical] {
    puts $fh "$cell  |  ref_name: [get_property REF_NAME $cell]  |  primitive: [get_property PRIMITIVE_GROUP $cell]"
}
close $fh

set fh [open "$OUTDIR/net_list.rpt" w]
foreach net [get_nets -hierarchical] {
    puts $fh "$net"
}
close $fh

# ---------------------------------------------------------------------
# 6. Check whether the security-critical internal signals still exist
#    as distinct nets/cells post-synthesis, or were absorbed by
#    optimization (constant propagation / equivalent-driver removal).
# ---------------------------------------------------------------------
set watch_signals {term_cross01 term_cross10 term_sh0 term_sh1 t0_sh0 t0_sh1 a_sh0_r a_sh1_r b_sh0_r b_sh1_r}

set fh [open "$OUTDIR/signal_survival_check.rpt" w]
puts $fh "signal_name,found_as_net,found_as_cell,match_count"
foreach sig $watch_signals {
    set net_matches [get_nets -hierarchical -filter "NAME =~ *${sig}*" -quiet]
    set cell_matches [get_cells -hierarchical -filter "NAME =~ *${sig}*" -quiet]
    set n_found [expr {[llength $net_matches] > 0 ? "yes" : "no"}]
    set c_found [expr {[llength $cell_matches] > 0 ? "yes" : "no"}]
    set count [expr {[llength $net_matches] + [llength $cell_matches]}]
    puts $fh "${sig},${n_found},${c_found},${count}"
    if {$count == 0} {
        puts "WARNING: signal '$sig' not found in post-synth netlist -- \
possible optimization/absorption. Check synth_design.log for \
constant propagation / equivalent-driver-removal messages."
    }
}
close $fh

# ---------------------------------------------------------------------
# 7. Pull synthesis warnings related to optimization that could
#    collapse the masking structure (const prop, sweep, equivalent
#    register/driver removal, retiming).
# ---------------------------------------------------------------------
if {[file exists "$LOGDIR/synth_design.log"]} {
    set fh [open "$OUTDIR/synth_warnings_filtered.rpt" w]
    set logdata [open "$LOGDIR/synth_design.log" r]
    foreach line [split [read $logdata] "\n"] {
        if {[string match -nocase "*WARNING*" $line] &&
            ([string match -nocase "*constant*" $line] ||
             [string match -nocase "*equivalent*" $line] ||
             [string match -nocase "*sweep*" $line] ||
             [string match -nocase "*optimiz*" $line] ||
             [string match -nocase "*remov*" $line] ||
             [string match -nocase "*merge*" $line])} {
            puts $fh $line
        }
    }
    close $logdata
    close $fh
} else {
    puts "NOTE: no fresh synth_design.log this run (checkpoint was reused) -- \
skipping synth_warnings_filtered.rpt. Delete $OUTDIR/post_synth.dcp and re-run \
if you need the warnings log regenerated."
}

# ---------------------------------------------------------------------
# 8. Write out synthesized netlist (structural verilog) for manual diff
#    against the RTL security model if needed later.
# ---------------------------------------------------------------------
write_verilog -force -mode funcsim "$OUTDIR/post_synth_netlist.v"

puts "TEST 2 synthesis complete. Outputs in $OUTDIR"
puts "Check signal_survival_check.rpt and synth_warnings_filtered.rpt first."
