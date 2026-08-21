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

## Open / unresolved

- **`docs/PROJECT_SUMMARY.md` and `results/INDEX.md`** — the README references both
  as authoritative sources for full methodology and per-file provenance. **Neither
  exists anywhere in the uploaded archive.** Not fabricated here. If they exist
  outside this upload, add them; otherwise the README's pointers to them are
  currently dangling.
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
