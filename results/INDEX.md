# Results index

Referenced from the top-level README. This file did not exist in the uploaded
archive (see `docs/PROVENANCE_GAPS.md`) — written here from the actual file layout
produced during the rebuild.

| Directory | Milestone | Contents |
|---|---|---|
| `m0_baseline/milestone0-and/` | M0 | AND gadget, unconstrained. Inputs + full outputs (synth/place/route DCPs, coverage report, reports). |
| `m0_baseline/xor-gadget/`, `m0_baseline/nand-gadget/` | M0 | XOR/NAND gadgets, unconstrained. Same structure. |
| `m0_baseline/and-constrained/`, `xor-constrained/`, `nand-constrained/` | M0 | Hard `CONTAIN_ROUTING` pblock attempts (Decisions 11/12). `nand-constrained` output set is incomplete — see PROVENANCE_GAPS.md. |
| `m0_baseline/and-soft-constrained/` | M0 | Soft-pblock attempt (`IS_SOFT true`) — separation lost, per Decision 13 step 2. |
| `m0_baseline/and-corridor/` | M0 | Quarantine-corridor attempt (Decision 13 step 3) — failed to route; only synthesis-stage artifacts survive, consistent with that outcome. |
| `m0_baseline/and-placement-only/` | M0 | **The working mitigation** (Decision 13): `IS_SOFT false`, no `CONTAIN_ROUTING`. Min tile-distance 83, 0 routing errors. |
| `m1_conflict_detection/` | M1 | Baseline XCZU2 build (placed/wired/routed DCPs) and `baseline_conflicts.csv` — the original 28-conflict scan before any mitigation. |
| `m2_m2b_reroute/` | M2/M2b | Gap — see `NOTE_missing_output.md`. |
| `m3_m3b_rwroute_customcost/` | M3/M3b | Soft-penalty (`customcost_routed*.dcp`, `softpenalty_conflicts.csv`) and hard-exclusion (`hardexcl_routed.dcp`, `hardexcl_diag_routed.dcp`, `and_gadget_xczu2_internalM4_routed.dcp`) RWRoute variants. `forbidden_nodes.txt` is the tile-exclusion list used. `session_commands.txt` is the raw shell history showing the sequence of builds/runs. |
| `m3c_placement_geometry/` | M3c (added this rebuild) | Placement-geometry iteration v2–v5, `switchbox_conflict_report.json` / `switchbox_conflicts_final_v5.csv` for the final (open_fabric=0) state. See `docs/M3C_PLACEMENT_GEOMETRY.md`. |
| `m4_tvla/test2_synth_out/` | M4 | The one synthesis run, Artix-7, v2 RTL lineage. |
| `m4_tvla/test3_place_route_out/` | M4 | The one place & route run. |
| `m4_tvla/test4_physical_leakage_out/` | M4 | Physical-coupling reports (BEL co-location, site sharing, control sets, site PIPs). |
| `m4_tvla/test5_gatelevel_out/` | M4 | Gate-level netlist export, with and without SDF. |
| `m4_tvla/rtl_level_sim/tvla_v3_tb/` | M4 | **Confirmed RTL-level TVLA result**: max \|t\| = 1.240. |
| `m4_tvla/rtl_level_sim/tvla_run_tb1/` | M4 | Earlier (v1) testbench trace, flags `term_cross01` — diagnosed as a PRNG artifact, not a leak. See `docs/M4_TVLA_SUMMARY.md`. |
| `m4_tvla/rtl_level_sim/tvla_sim_exploratory_waveform_only/` | M4 | Earliest testbench, waveform inspection only, no trace CSV. |
| `m4_tvla/tvla_trace_gatelevel.csv` | M4 | **Confirmed post-route gate-level TVLA result** (no SDF): max \|t\| = 1.280. |
| `m4_tvla/diagnostics_sdf_blocked/` | M4 | Two independent SDF/timing-annotated TVLA attempts. **Diagnostic/blocker evidence only — no statistic was produced by either.** |
