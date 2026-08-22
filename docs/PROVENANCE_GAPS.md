# Provenance gaps and unresolved items

Found during the rebuild from `milestone0_full.zip`. Listed rather than silently
patched over or fabricated.

## Resolved during inspection (documented for the record)

- **`and_gadget_xczu2_m4_routed.dcp` naming collision** — resolved. It belongs to
  M3b (an internal-numbering "Milestone 4" from before the project settled on the
  public M0–M3b scheme), not the Artix-7 TVLA M4. Full reasoning in
  `docs/M3C_PLACEMENT_GEOMETRY.md`. Preserved under the renamed
  `and_gadget_xczu2_internalM4_routed.dcp` to avoid re-creating the ambiguity.
- **`_v2.py`–`_v5.py` (M3c)** — resolved by user direction: added as a new milestone
  after M3b, documented in `docs/M3C_PLACEMENT_GEOMETRY.md`, M3b's own conclusion left
  unmodified.
- **Earlier RTL-level TVLA trace flagging `term_cross01` at `|t|=7.850`** — resolved;
  the v3 testbench's own header comment documents the PRNG-artifact diagnosis and fix.
  See `docs/M4_TVLA_SUMMARY.md`.

## Resolved since M5 (this pass)

- **`results/INDEX.md`** — created. Documents every M5 artifact
  (`classify_*.json`, `config_*.txt`, `repair_policy.json`,
  `generate_constraints.py`, `generated_repair_*`,
  `share_separation_auto_repaired.xdc`, `test3_place_route_autorepair.tcl` and
  its output dir) with purpose, source, producing step, observed result, and
  whether each is authoritative evidence or an intermediate artifact.
- **`docs/PROJECT_SUMMARY.md`** — the README no longer references this filename
  anywhere (checked directly: no match for `PROJECT_SUMMARY` in `README.md`).
  The site footer (`index.html`) previously linked to it as a dangling
  reference; that link has been repointed at `README.md`, which does exist.
  This item is closed as **superseded, not fulfilled** — the gap was in a
  stale link, not in a missing document the project actually needs.

## Open / unresolved
- **`LICENSE`** — the README states MIT and links `[LICENSE]`. No LICENSE file was
  in the upload. Not created here — adding real license text on someone's behalf
  isn't a file-organization task. Add the actual file before the README's link will
  resolve.
- **M2/M2b output artifact missing** — see
  `results/m2_m2b_reroute/NOTE_missing_output.md`. The script
  (`milestone2b_targeted_reroute.py`) is present; its output DCP is not.
- **`experiments/0004-...` is absent** — numbering jumps from `0001`–`0003` to
  `0005`. No reference to a `0004` anywhere in the upload (checked all `.md`, `.py`,
  `.tcl` files). Left as a gap in the sequence rather than renumbered or filled.
- **Per-stage switch-box conflict counts for M3 (soft-penalty) and M3b
  (hard-exclusion) were not separately saved.** `session_commands.txt` shows the
  detector was re-run after each RWRoute variant (`type switchbox_conflicts.csv`),
  but each run overwrote the same `switchbox_conflicts.csv` — only the *final* state
  (from the M3c/`_v5` run) survived as a file. The DCP checkpoints for every
  intermediate stage (`customcost_routed`, `customcost_routed2`, `hardexcl_routed`,
  `hardexcl_diag_routed`, internal-M4) are all preserved in
  `results/m3_m3b_rwroute_customcost/`, so the counts are regenerable by re-running
  `src/m1_conflict_detection/switchbox_conflict_detector.py` against each, but that
  requires a RapidWright/JPype environment this rebuild did not have. The README's
  own escalation numbers (3 → 6 → 7, per its `escalation.svg` reference) are taken on
  trust from the existing README text, not independently re-verified against a saved
  per-stage CSV.
- **`m6_conflicts.csv`** — a top-level file with tile coordinates (`INT_X27Y178` etc.)
  in a different coordinate range than the M3b `forbidden_nodes.txt` set
  (`INT_X14-16Y88-90`), and a device-scale suggesting UltraScale+. Content pattern
  (open_fabric / co_located_terminal conflict rows) matches the M1 detector's CSV
  schema, and the coordinates match the M3c "M6" step's own conflict description in
  `wire_and_gadget_xczu2_v3.py`'s docstring (`INT_X27Y178`/`179`) — **likely** the
  saved conflict CSV from that specific M3c step. Not moved into
  `results/m3c_placement_geometry/` because the filename's "m6" doesn't match this
  document's M3c numbering and no explicit save-command evidence (unlike
  `baseline_conflicts.csv`/`softpenalty_conflicts.csv`) confirms it. Left at the
  original top level of the source archive, not copied into the rebuilt repo. Flagged
  here rather than guessed into place.
- **`and-corridor` and `nand-constrained` M0 variants have incomplete output sets**
  (corridor: synthesis-stage artifacts only, no place & route checkpoint;
  nand-constrained: only distance-indicator files, no DCP/reports). For `and-corridor`
  this is consistent with the documented outcome (Decision 13: the corridor attempt
  "still failed to route"), so a missing routed checkpoint isn't surprising. For
  `nand-constrained` there's no equivalent documented explanation — Decision 12
  discusses NAND findings but the constrained-NAND run's full output set doesn't
  appear to have been preserved. Flagged, not filled in.
- **Vendored dependencies excluded from the rebuilt repo**: `RapidWright-master/`
  (full upstream source clone) and `rapidwright.zip` (a duplicate zip of what appears
  to be the same). These are a third-party dependency, not project output; the README
  already links the upstream RapidWright repo. `gnl_test.dcp` / `gnl_test_routed.dcp`
  were also excluded — confirmed via `test_device_load.py`'s own comment to be
  RapidWright's bundled example checkpoint (device `xcku040-ffva1156-2-e`, unrelated
  to this project's gadget), used only to smoke-test that RapidWright could load
  UltraScale+ device data.

## M5-specific provenance notes (new)

- **The generated repair is functionally equivalent to the manual `share_separation_v2.xdc`,
  not syntactically identical.** The generator emits exact-instance `NAME =~` filters
  (e.g. `NAME =~ u_and_cross10/y_INST_0`) rather than the broader glob patterns
  (`NAME =~ *cross10*`) the hand-written v2 XDC used. Confirmed by direct diff of
  `generated_repair_v1.xdc` against `share_separation_v2.xdc`'s
  `add_cells_to_pblock` lines. Deliberate generator design choice (reduces the
  chance of an exact-instance constraint accidentally matching an unrelated
  future cell), not an oversight.
- **`cross10 -> sh0` is configuration-driven, not independently inferred.**
  `generated_repair_v1_log.json` records the rule as `EXPLICIT_POLICY`, sourced
  from `repair_policy.json`'s `SEPARATE_CROSS_TERMS` group
  (`{"pattern": "*cross10*", "side": "sh0"}`), because `u_and_cross10/y_INST_0`
  had no site-level evidence to lean on (alone at `SLICE_X59Y99` in the v1
  checkpoint). A different policy file would produce a different, equally
  "valid" assignment — do not cite this as a discovered geometric fact.
- **Auto-repair inherited the original pblock coordinate warning.** Confirmed
  directly in `vivado_1288.backup.log` (lines 55-56):
  `[Place 30-8517]` (pblock_share0 range aligned to tile boundaries) and
  `CRITICAL WARNING: [Place 30-8520] Ranges extend outside of device:
  SLICE_X90Y99:SLICE_X60Y0` (pblock_share1's range, `SLICE_X60Y0:SLICE_X90Y99`,
  carried unchanged from the original `share_separation.xdc`, exceeds
  `xc7a100tcsg324-1`'s real bounds). Vivado auto-clipped and completed
  placement/routing without error; this is a pre-existing property of the
  original XDC's range choice, not something the M5 automation introduced.
- **The final classifier result (0/0/0/0) is directly observed from the
  reimplemented checkpoint**, not inferred from the generated XDC's contents.
  `config_autorepair.txt` points `detect_classify.tcl` at
  `./test3_place_route_autorepair_out/post_route.dcp` — the actual post-route
  output of the from-scratch reimplementation — and `classify_autorepair.json`
  is that run's direct output, not a copy or hand-edit of `classify_v2.json`.
  (Diffed: `classify_autorepair.json` and `classify_v2.json` agree on every
  cell/site/summary field but were produced by two separate classifier runs
  against two separate checkpoints, per their differing `checkpoint` fields.)

## Newly found during this pass: two stray, mangled debug-output files

`security_tests/` contains two files whose names are the literal strings
`*_sh1*` and `*cross01*`, with the `*` characters rendered as the private-use
codepoint `U+F02A` (a common artifact of a Windows filesystem substituting an
illegal filename character before a sync/copy step — these files most likely
started life as a Tcl script accidentally using an unresolved glob pattern
string, e.g. `$env(OUT)`, as a literal output filename rather than an actual
glob).

Each contains a JSON classifier output, but from a **different, narrower
config** than any of the four real M5 runs — e.g. the `*_sh1*`-named file's
embedded config has `"sh1_patterns": ["*_sh1*"]` and `"watch_patterns":
["*_sh0*"]` only (missing `*cross01*`/`*cross10*` entirely), unlike
`classify_v1.json`'s full four-pattern watch set. These do not match the
config of `config_baseline.txt`/`config_v1.txt`/`config_v2.txt`/
`config_autorepair.txt` and are not referenced by any `.tcl`, `.py`, or `.md`
file in the repository.

**Assessment: leftover debug/exploratory runs from before the config-file
(`config_*.txt`) driven workflow was settled on, not part of the M5 evidence
chain.** Not deleted here (this pass does not modify experimental outputs),
not counted as Test A/B/C/autorepair evidence, and not folded into
`results/INDEX.md`'s M5 artifact table. Flagged so a future pass either
removes them or renames them to something that doesn't collide with shell
glob expansion.
