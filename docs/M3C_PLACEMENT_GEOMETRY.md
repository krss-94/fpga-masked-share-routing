# M3c — Placement-geometry follow-on to M3b (XCZU2)

**Status: added during this rebuild, at the user's direction, after inspection of the
uploaded files surfaced it. Not present in the original README. Does not change
M3/M3b's own conclusion — see "What this does and does not resolve" below.**

## Why this exists

M3b patched RWRoute's own cost function (soft penalty → hard exclusion) and found
that tightening the routing-avoidance constraint made genuinely avoidable conflicts
*worse*, not better — the README's central M3/M3b finding. The uploaded files contain
four further scripts (`src/m3c_placement_geometry/wire_and_gadget_xczu2_v2.py`
through `_v5.py`) that continue past that result by changing **placement geometry**
instead of the routing cost function. These scripts carry their own internal
milestone numbering ("Milestone 5" through "Milestone 8" in their docstrings) from
before the project settled on the M0–M3b public numbering; that internal numbering is
unrelated to this document's "M3c" label, which is assigned here for consistency with
the README's scheme.

Internal-numbering note, resolved from evidence, not guesswork: the internal
numbering's own **"Milestone 4"** — referenced in `_v2.py`'s docstring as the prior
step ("M4 (PIP-level hard exclusion in RWRoute.java)") — is `and_gadget_xczu2_m4_routed.dcp`,
preserved under `results/m3_m3b_rwroute_customcost/and_gadget_xczu2_internalM4_routed.dcp`.
It is the same generation of result as M3b's `hardexcl_routed.dcp` /
`hardexcl_diag_routed.dcp` (confirmed by file timestamps: `RWRoute.java` rebuilt
17 Aug 12:58, this checkpoint produced 17 Aug 13:05, one run after the 16 Aug
`hardexcl` pair). **It is unrelated to the Artix-7 TVLA milestone this project calls
M4.** The two use the same numeral by coincidence of two different, non-overlapping
internal numbering schemes used at different points in the project's history.

## What each step changed and found

Baseline going in (M3b's own result, unmitigated by placement): `open_fabric_count = 3`.

| Step | Script | Change | Result | Notes |
|---|---|---|---|---|
| (internal M5) | `_v2.py` | Placed the two cross-share cells apart from *each other*, not just from their same-share partner | `open_fabric_count = 4` | Regression — introduced two new conflicts unrelated to the fix |
| (internal M6) | `_v3.py` | Found and fixed a driver-placement bug in the M5 script: `sites_sorted` was sorted by column only, so driver sites for far-apart consumers landed on adjacent rows by enumeration-order coincidence | `open_fabric_count = 2` | Root-caused from reading the M5 script's own placement code |
| (internal M7) | `_v4.py` | Single-variable test: chose driver sites for one specific approach vector into `cross_site_b`, leaving the already-clean side untouched | `open_fabric_count = 1` | Scoped explicitly to test one hypothesis only |
| (internal M8) | `_v5.py` | Replaced M7's strided candidate sampling with a full brute-force search over both site pools | **`open_fabric_count = 0`** | Confirmed directly in `switchbox_conflict_report.json` from this run |

The final (`_v5`) run's own `switchbox_conflict_report.json` (preserved at
`results/m3c_placement_geometry/switchbox_conflict_report.json`) reports:

```
"cross_share_switch_box_conflicts": {
  "count": 2,
  "open_fabric_count": 0,
  "co_located_terminal_count": 2
}
```

## What this does and does not resolve

- **Does not contradict M3/M3b.** M3/M3b's finding — that patching the router's own
  cost function cannot be relied on to avoid these conflicts, and tightening it can
  make things worse — stands unchanged. M3c did not touch the cost function; it
  changed where cells are placed before routing runs at all.
- **Does close the `open_fabric` category** for this specific 2-share AND gadget on
  this specific XCZU2 build, via iterative placement-geometry search, not via any
  general or automated tool-level guarantee. Each step was a manually root-caused,
  single-variable change — this is a hand-tuned result, not a demonstrated general
  technique.
- **Does not touch the remaining 2 conflicts**, which are `co_located_terminal` type.
  Per the M1 detector's own embedded documentation (preserved in
  `switchbox_conflict_report.json`'s `note` field): these occur where the shared tile
  is a physical source/sink for both nets — i.e., reflect the gadget's own designed
  cross-share structure, not an avoidable routing/placement choice, "since a cell's
  own site does not move." These were never in scope for M3b's or M3c's mitigation
  attempts.
- **Generalization not established.** All M3c results are for the same one 2-share
  AND gadget on the same one XCZU2 checkpoint lineage as M0–M3b. No claim is made
  about AES-scale designs or other devices.
