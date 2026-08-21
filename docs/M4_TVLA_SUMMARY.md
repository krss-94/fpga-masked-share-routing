# M4 — Leakage Validation (TVLA)

## Relationship to M0–M3b

**M4 is a related but separate checkpoint lineage from M0–M3b.** M0–M3b (and the
M3c follow-on below) all operate on the XCZU2-targeted, from-scratch RapidWright
build of the AND gadget, using the **v1 RTL naming lineage**:

```
u_and00 / u_and01 / u_and10 / u_and11
```

M4 operates on **Artix-7 (`xc7a100tcsg324-1`)**, synthesized conventionally through
Vivado from `rtl/masked_and_gadget_v2.v`, using the **v2 RTL naming lineage**:

```
u_and_sh0 / u_and_cross01 / u_and_cross10 / u_and_sh1
```

Same gadget, same logical structure, different device, different toolchain path,
different instance names, and **not derived from the M0 checkpoint**. Do not treat
M4 results as confirming or refuting the M1 switch-box coupling findings — they are
independent lines of evidence on different hardware.

## Pipeline (test1–test5)

| Stage | Script | What it did | Runs |
|---|---|---|---|
| TEST 2 | `tcl/m4/test2_synth.tcl` | Out-of-context synthesis of `masked_and_gadget_v2.v` on `xc7a100tcsg324-1` | **One synthesis run** |
| TEST 3 | `tcl/m4/test3_place_route.tcl` | Place + route from the TEST 2 checkpoint | **One P&R run** |
| TEST 4 | `tcl/m4/test4_physical_leakage.tcl` | Physical-coupling analysis: BEL co-location, shared SITE contents, site PIPs, control-set sharing, for the share-bearing cells | Report-only, one pass |
| TEST 5 | `tcl/m4/test5_export_gatelevel.tcl` | Export post-route gate-level netlist, with and without SDF | One export |

## Statistical leakage results (Welch's t-test, threshold `|t| > 4.5`)

Computed by `src/m4_tvla/tvla_analysis.py`, re-run against the preserved trace CSVs
during this rebuild — the numbers below are independently reproduced, not just quoted:

| Trace | Testbench | Worst-case signal | max \|t\| | Verdict |
|---|---|---|---|---|
| RTL-level, v3 stimulus | `tb_masked_and_gadget_tvla_v3.v` | `a_sh0_r` | **1.240** | No leak flagged |
| Post-route gate-level, no SDF | `tb_masked_and_gadget_tvla_gatelevel.v` | `a_sh0_r` | **1.280** | No leak flagged |

Both are below the 4.5 threshold. **This does not confirm the physical implementation
is leak-free** — see Limitations below.

### An earlier RTL-level trace *did* flag — and why it's not used as the confirmed result

`results/m4_tvla/rtl_level_sim/tvla_run_tb1/` preserves an earlier run, testbench
`tb_masked_and_gadget_tvla.v` (pre-v3), which flags `term_cross01` at `|t| = 7.850`.
This is **not presented as a leakage finding**. The v3 testbench's own header comment
(preserved verbatim in `rtl/` — see the testbench file) documents the diagnosis: v1/v2
used Vivado xsim's `$urandom_range`, which has known low-bit serial correlation; three
in-testbench fixes (reseeding, matching RNG call counts across populations) did not
remove it — the flagged signal got *stronger* after equalizing call counts, which
pointed at the PRNG itself rather than the testbench logic. v3 replaced in-simulator
randomness with externally generated stimulus (`gen_tvla_stimulus.py`, numpy PCG64)
fed from `stimulus.mem`. The same bit pattern that produced `t = -7.850` under
`$urandom_range` produced `t = -0.381` under PCG64. This is preserved as an
instrumentation-artifact case study, not a superseded leakage claim.

`results/m4_tvla/rtl_level_sim/tvla_sim_exploratory_waveform_only/` is a third,
earlier testbench (`tb_masked_and_gadget.v`) used only for waveform inspection — it
produced no trace CSV and no statistic.

## Test 4: physical coupling analysis

`test4_physical_leakage_out/` holds five reports (BEL co-location map, shared-site
full contents, control sets, site PIPs used, site-sharing summary) generated from the
TEST 3 post-route checkpoint. Per the script's own header: TEST 3's routed-tile
comparison found zero shared general-fabric routing tiles between shares, but that
zero is expected and not meaningful on its own — intra-site connections (site PIPs,
LUT fracturing, shared control sets) don't appear as routed nodes, so a routing-tile
diff structurally cannot see them. TEST 4 inspects those mechanisms directly instead.
The five reports are the result; no single pass/fail statistic is computed at this
stage — read the reports themselves for findings.

## SDF / timing-annotated TVLA: operationally blocked, no statistic produced

**Two independent attempts** to run TVLA on a timing-annotated (SDF-backed) gate-level
simulation were made. Neither produced a leakage statistic. Both are preserved as
diagnostic/blocker evidence in `results/m4_tvla/diagnostics_sdf_blocked/`, split by
attempt:

- **`attempt1_tvla_timing_project/`** — a dedicated Vivado sim project
  (`tvla_timing`) targeting the SDF-backed netlist. Elaboration failed before
  simulation could run: `ERROR: [XSIM 43-3225] Cannot find design unit
  xil_defaultlib.glbl in library work located at xsim.dir/work.`
- **`attempt2_top_level_sdf_run/`** — a direct `xelab`/`xvlog`/`xsim` invocation
  against the exported timing netlist and SDF. This got further (elaboration and
  many delay-annotation warnings proceeded) but failed at SDF annotation itself:
  `ERROR: [XSIM 43-3462] Unable to annotate SDF delays in the design.`, preceded by
  repeated `Unable to find delay expressions for setup/hold` and `pathpulse limits`
  warnings for `FDRE_default`, `LUT2`, and `LUT4` instances.

**Do not read these as "SDF was clean" or as a leakage result of any kind.** No
timing-annotated TVLA statistic exists for this project. The no-SDF gate-level result
(max |t| = 1.280, above) is the closest available evidence and is explicitly a
behavioral, non-timing-accurate proxy.

## What M4 does and does not establish

- Adds **statistical leakage evidence** (Welch's t-test on a Hamming-weight switching
  proxy) alongside M0–M3c's **structural/geometric** evidence (tile-distance,
  switch-box conflict detection).
- Does **not** close the physical-coupling hypothesis from M1, both because the
  device/checkpoint lineage differs (see above) and because the one TVLA path that
  would account for real post-route timing (SDF-annotated simulation) was
  operationally blocked, twice, independently.
- Does **not** claim any routing-iteration (v2–v5) work happened on the Artix-7 M4
  checkpoint. That work (M3c) is a separate, XCZU2-only experiment — see
  `docs/M3C_PLACEMENT_GEOMETRY.md`.
- Does **not** claim zero switch-box conflicts were achieved in the M4 (Artix-7)
  experiment. No switch-box conflict detector run was performed against the Artix-7
  checkpoint; that tool (M1) targets XCZU2/UltraScale+ RapidWright checkpoints and
  was never pointed at the M4 device.
