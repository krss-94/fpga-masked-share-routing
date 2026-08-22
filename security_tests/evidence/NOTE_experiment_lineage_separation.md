# NOTE: Two separate experiment lineages - do not conflate

## Lineage A: xc7a100tcsg324-1 (Artix-7)
Current active flow: test2_synth.tcl -> test3_place_route.tcl ->
test4_physical_leakage.tcl -> test5_export_gatelevel.tcl. Checkpoints:
test2_synth_out/post_synth.dcp, test3_place_route_out/post_route.dcp,
test3_place_route_separated_out/post_route.dcp (share-separated variant,
added during this investigation). This lineage produced
tvla_trace_gatelevel.csv, the SDF timing sim, and both the baseline and
share-separated placement comparisons.
Finding: baseline shows same-slice/adjacent-slice cross-share
co-location (SLICE_X52Y100); share-separated build eliminates it
(distance 0-1 tiles -> 29 tiles uniformly, zero cross-share site sharing).

## Lineage B: xczu2 (Zynq UltraScale+)
Files: and_gadget_xczu2_*.dcp, wire_and_gadget_xczu2*.py,
build_and_gadget_xczu2.py, switchbox_conflict_detector.py,
switchbox_conflict_report.json, switchbox_conflicts.csv. Separate
RapidWright-based build/wiring flow, not the test2/3/4/5 scripts above.
Finding: 2 cross-share switchbox events, both co_located_terminal
(structurally forced, not avoidable open-fabric coupling),
open_fabric_count: 0.

## Why this matters
Early in this investigation the xczu2 switchbox result was briefly cited
alongside xc7a100t placement data before the device mismatch was caught.
They are separate experiments on separate hardware targets and must be
cited by lineage (A or B), never as one undifferentiated result.

## Held for future work (not started)
M1 -> M3c xczu2 gate-level/netlist TVLA (HW/HD) comparison would need a
new xczu2 export/simulation path (none exists for lineage B currently).
Deliberately deferred, not a blocker for the current investigation.
