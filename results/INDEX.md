# Results index

Full per-file provenance for every checkpoint and result referenced by the README.
This pass adds the **M5 — Automated constraint repair** artifact set. Earlier
milestones' entries are not reproduced here; see the README's own
[Repository structure](../README.md#repository-structure) section and
[`docs/PROVENANCE_GAPS.md`](../docs/PROVENANCE_GAPS.md) for M0–M3c/M4 provenance.

All M5 files live in `security_tests/`. All are authoritative evidence unless
marked intermediate.

## Classifier configs (input)

| File | Purpose | Points at |
|---|---|---|
| `config_baseline.txt` | Config for Test A | `../test3_place_route_out/post_route.dcp` — no share-separation XDC applied |
| `config_v1.txt` | Config for Test B | `./test3_place_route_separated_out/post_route.dcp` — original hand-written, broken `share_separation.xdc` |
| `config_v2.txt` | Config for Test C | `./test3_place_route_v2_out/post_route.dcp` — manually repaired reference `share_separation_v2.xdc` |
| `config_autorepair.txt` | Config for the end-to-end acceptance run | `./test3_place_route_autorepair_out/post_route.dcp` — from-scratch reimplementation of the *generated* repair |

## Classifier outputs (authoritative)

| File | Producing step | Observed result |
|---|---|---|
| `classify_baseline.json` | `detect_classify.tcl` + `config_baseline.txt` | **1** `MIXED_SITE_CONFLICT` (`SLICE_X52Y100`, 10 cells), 0 elsewhere. Test A input. |
| `classify_v1.json` | `detect_classify.tcl` + `config_v1.txt` | 0 mixed; 1 `UNCLASSIFIED_ONLY` site, 1 `UNCLASSIFIED_CELL_PRESENT` site, 4 unclassified cells (2 logical cross-terms × 2 hierarchy levels each). Test B input. |
| `classify_v2.json` | `detect_classify.tcl` + `config_v2.txt` | **0 / 0 / 0 / 0** — clean. Test C input and the ground-truth target for the automated loop. |
| `classify_autorepair.json` | `detect_classify.tcl` + `config_autorepair.txt` | **0 / 0 / 0 / 0** — final acceptance result. Independently produced (own `checkpoint` field points at the autorepair build, not copied from `classify_v2.json`). |

## Repair generator (input + code + authoritative logs)

| File | Purpose | Authoritative? |
|---|---|---|
| `repair_policy.json` | Explicit repair policy: pblock names + `SEPARATE_CROSS_TERMS` name-pattern groups (`*cross01*`→sh1, `*cross10*`→sh0) | Authoritative — the single source for every `EXPLICIT_POLICY` decision |
| `generate_constraints.py` | The repair generator itself. `SITE_UNANIMOUS_INFERENCE` / `EXPLICIT_POLICY` / refuse-`MIXED_SITE_CONFLICT` logic. No hardcoded cell names. | Authoritative (code) |
| `generated_repair_baseline_log.json` | Generator log, Test A | 0 assignments; all 10 `MIXED_SITE_CONFLICT` cells logged `action: NONE_UNSUPPORTED` |
| `generated_repair_v1_log.json` | Generator log, Test B | 2 assignments, both traceable: `u_and_cross01/y_INST_0`→sh1 (`SITE_UNANIMOUS_INFERENCE`), `u_and_cross10/y_INST_0`→sh0 (`EXPLICIT_POLICY`) |
| `generated_repair_v2_noop_log.json` | Generator log, Test C | 0 assignments, empty `entries` array |

## Generated XDCs (authoritative for Test A/C; Test B's is the one applied)

| File | Content | Role |
|---|---|---|
| `generated_repair_baseline.xdc` | No `add_cells_to_pblock` statements; header comment lists the 10 unaddressed `MIXED_SITE_CONFLICT` cells for manual review | Test A output — correct refusal, not an empty/broken file |
| `generated_repair_v1.xdc` | 2 `add_cells_to_pblock` statements (one per assignment above) | Test B output — **this is the file applied in the end-to-end acceptance run** |
| `generated_repair_v2_noop.xdc` | No statements; explicit no-op | Test C output |
| `share_separation_auto_repaired.xdc` | `share_separation.xdc` (original, broken) + `generated_repair_v1.xdc`, concatenated | **The end-to-end acceptance input.** Applied against the *original broken* XDC, not the hand-repaired v2 — this is the fact the M5 acceptance claim depends on. |

## Implementation + re-verification (authoritative)

| File | Purpose | Result |
|---|---|---|
| `test3_place_route_autorepair.tcl` | Runs `share_separation_auto_repaired.xdc` from scratch through synthesis → `opt_design` → `place_design` → `route_design` | Completed; produced `CRITICAL WARNING [Place 30-8520]` (pblock_share1 range clipped to device bounds — inherited from the original XDC, not introduced by the generator; see `docs/PROVENANCE_GAPS.md`) but routed with 0 errors |
| `test3_place_route_autorepair_out/` | Output directory — contains `post_route.dcp`, the checkpoint `classify_autorepair.json` was generated from | Intermediate build artifact; the classifier output (`classify_autorepair.json`, above) is the authoritative evidence derived from it |

## Test summary

| Test | Classifier input | Assignments | Result |
|:---:|---|:---:|---|
| **A** | `classify_baseline.json` | 0 | Refused — `MIXED_SITE_CONFLICT` correctly escalated, 10/10 cells `NONE_UNSUPPORTED` |
| **B** | `classify_v1.json` | 2 | Both traceable, one `SITE_UNANIMOUS_INFERENCE`, one `EXPLICIT_POLICY` |
| **C** | `classify_v2.json` | 0 | Explicit no-op, already clean |
| **Final (autorepair)** | `classify_autorepair.json` | — | **0/0/0/0**, from-scratch reimplementation of Test B's repair on the original broken XDC, same frozen classifier as A/B/C |

## Not included above (see `docs/PROVENANCE_GAPS.md`)

Two stray files in `security_tests/` (literal filenames `*_sh1*` and
`*cross01*`, `*` mangled to `U+F02A`) contain classifier-shaped JSON from a
narrower, non-matching config and are not part of the evidence chain above —
they're flagged, not indexed, in `docs/PROVENANCE_GAPS.md`.
