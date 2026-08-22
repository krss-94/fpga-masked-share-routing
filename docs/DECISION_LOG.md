\# Decision Log



\## Decision 10 — Accept naming-based mapping strategy for Milestone 0

Coverage measured at 93.33% (14/15 logical cells) on the toy 2-share AND

gadget. The single unmapped object (r\_r\_reg) is the fresh-randomness

register, which correctly carries no share label since it is not a share

of a, b, or q. Manual inspection via coverage.csv confirmed no ambiguous

or genuinely unmapped share-bearing objects. An initial run showed 26.67%

coverage due to an inconsistent naming convention in the RTL test

instrumentation — caught during the mandated manual inspection step and

fixed at the RTL level, not by adjusting the measurement logic.



\## Decision 11 — Accept mapping strategy for XOR gadget; note linear vs

non-linear gadget contrast



Coverage measured at 80.00% (16/20 objects) on the masked XOR gadget. All

4 unmapped objects are clock/implementation infrastructure (clk,

clk\_IBUF\_inst, clk\_IBUF\_BUFG\_inst, <LOCKED>), not share-bearing signals —

manually confirmed by cross-referencing object names against the RTL,

consistent with Milestone 0's r\_r\_reg precedent. Of the 16 share-bearing

objects, 100% mapped unambiguously with zero cross-share terms, confirming

that XOR (a linear operation) requires no randomness and produces no

cross-share mixing, in contrast to the AND gadget (Milestone 0), which

required a genuine cross-share term. This is the first empirical evidence

in this project that gadget linearity is visible in the post-P\&R physical

mapping, not just in RTL-level theory.



\## Decision 12 — Accept mapping strategy for NAND gadget; note LUT-folding

of cross-share structure



Coverage measured at 72.73% (16/22 objects) on the masked NAND gadget.

All 6 unmapped objects are either clock/implementation infrastructure

(clk, clk\_IBUF\_inst, clk\_IBUF\_BUFG\_inst, <LOCKED>) or randomness-related

(r\_r, r\_r\_IBUF\_inst) - none are share-bearing signals, consistent with

gadgets #1 and #2. Of the 16 share-bearing objects, 100% mapped

unambiguously. Unlike Milestone 0's AND gadget, the cross-share terms

(cross01, cross10) do not appear as separate objects post-synthesis -

Vivado folded them into a single LUT5, making the cross-share structure

invisible as a distinct object at this granularity, even though it is

still functionally present inside the LUT's truth table. This is a

relevant finding for the project's core research question: synthesis

optimization can obscure cross-share structure from object-level

inspection without actually merging share identity in a way that leaks

information - the distinction between "structurally invisible" and

"actually leaking" needs to be kept explicit in any future indicator

(M4) design.

## Decision 13 — Full physical separation achieved for AND gadget via placement-only hard containment

**Date:** 2026-07-07
**Context:** Following Decisions 11/12 (XOR/NAND separation via hard CONTAIN_ROUTING
pblocks) and the AND routing failures documented leading into this decision (hard
CONTAIN_ROUTING breaks routing on AND's genuine cross-share signal; the quarantine
corridor attempt failed for the same underlying reason once real device coordinates
ruled out coordinate-clipping as the cause).

**What was tried and why it failed, in order:**
1. Hard containment (CONTAIN_ROUTING true) on share0/share1 pblocks: routing failed
   -- "Design has 2 unrouted pins, that are still reachable" -- because AND's
   cross-share nets (u_and_sh1/y, t0_sh1) must physically connect share-0 and
   share-1 territory, which CONTAIN_ROUTING forbids outright.
2. Soft containment (IS_SOFT true): routing succeeded but separation was lost
   almost entirely (min distance back to 0) -- the placer was free to ignore
   the pblock whenever convenient, with no guarantee of *why* it did or didn't.
3. Quarantine corridor (hard CONTAIN_ROUTING on two regions + a third
   EXCLUDE_PLACEMENT-only corridor for the cross-share cells specifically):
   still failed to route, but the failure moved to PLAIN SAME-SHARE signals
   (t0_sh1, u_and_sh1/y, both fully inside share-1's own region), not the
   cross-share signal. This ruled out "the crossing signal itself is the
   irresolvable blocker" as an explanation.
4. Removing CONTAIN_ROUTING to fix the routing failure (intending "placement
   containment only") silently reintroduced the Decision-11-style soft-pblock
   failure mode: Vivado defaults every pblock's IS_SOFT property to true
   unless explicitly set to false, and CONTAIN_ROUTING had been the only thing
   implicitly forcing IS_SOFT to false in attempts 1 and 3. Verified directly
   via `get_property IS_SOFT [get_pblocks pblock_share1_hard]` returning 1,
   and via reverse cell-to-pblock lookup showing correct pblock membership
   but a physical SITE far outside the pblock's own GRID_RANGES.

**The fix:** explicitly set `IS_SOFT false` on both share pblocks, WITHOUT
setting CONTAIN_ROUTING. This hard-constrains cell PLACEMENT into the disjoint
share-0/share-1 regions while leaving ROUTING completely unconstrained --
placement and routing containment are separable pblock properties, and only
the former is required for the physical-separation guarantee this project's
distance indicator measures.

**Result (build_and_placement_only.tcl / share_separation_placement_only.xdc):**
- route_design: 0 failed nets, 0 errors, 0 critical warnings.
- share_distance_indicator.py: min distance 83, mean distance 83.5
  (closest pair: b_sh0_r_reg / b_sh1_r_reg), comparable to XOR (127) and
  NAND (85).

**Decision:** Accept placement-only hard containment (IS_SOFT false, no
CONTAIN_ROUTING) as the working mitigation strategy for all three gadgets.
This supersedes the CONTAIN_ROUTING-based approach from Decisions 11/12 as
the recommended general technique -- it is strictly more general (works on
AND, where CONTAIN_ROUTING does not) and no weaker in the separation it
provides for XOR/NAND.

**Why this is the strongest finding of the mitigation experiment:** the
three-step failure sequence above is itself informative, not just the final
success. It demonstrates that "hard containment breaks routing for AND" was
never really about AND's cross-share signal being physically unresolvable --
it was an artifact of conflating routing containment with placement
containment inside a single Vivado property. Separating the two resolves the
apparent tension entirely, for all three gadgets, without giving up any
separation guarantee and without fabricating a result.

## Decision 14 — Automate the Constraint Repair v1 loop (M5); refuse MIXED_SITE_CONFLICT by design rather than guess

**Context:** Constraint Repair v1 (Test 8 / `security_tests`) hand-diagnosed and
hand-fixed one specific coverage gap: `share_separation.xdc`'s `*_sh0*`/`*_sh1*`
name-pattern selector had no basis to place `u_and_cross01`/`u_and_cross10`, so
those cells fell outside both pblocks. The fix worked, but it was a human reading
a classification report and hand-writing a corrected XDC. The question this
decision addresses: can that same detect -> diagnose -> fix -> reverify loop be
run automatically, without silently guessing at cases the evidence doesn't
support?

**Problem, restated precisely:** the classifier (`detect_classify.tcl`, frozen
and unmodified between all runs in this decision) buckets every occupied site
into one of five categories. Two of those categories are candidates for
automatic repair (`UNCLASSIFIED_CELL_PRESENT`, `UNCLASSIFIED_ONLY`); one is
explicitly not (`MIXED_SITE_CONFLICT`).

**Decision: only repair categories with sufficient evidence or explicit
configured policy. Never guess.**

- **`UNCLASSIFIED_CELL_PRESENT`** — an unclassified cell shares a site with
  classified cells that are unanimously one side. Resolved by
  `SITE_UNANIMOUS_INFERENCE`: assign to that unanimous side. This is inference
  from direct placement evidence, not a policy choice.
- **`UNCLASSIFIED_ONLY`** — no classified cells at that site at all, so there is
  no site-level evidence to infer from. Resolved *only* via an explicit,
  external `repair_policy.json` (`EXPLICIT_POLICY` / `SEPARATE_CROSS_TERMS`
  name-pattern match). If no policy rule matches, the generator fails loudly
  rather than falling back to a geometric guess (e.g. nearest pblock). This is
  a configured decision, not a discovered fact — a different policy file
  produces a different, equally "valid" assignment. Do not describe
  `cross10 -> sh0` as independently inferred; it is a policy match.
- **`MIXED_SITE_CONFLICT`** — refuse. Both shares' cells are already colocated
  at one physical site; this is a placement collision, not a coverage gap, and
  no automated pblock-membership addition can un-collide two cells already
  placed together. Every affected cell is reported with
  `action: NONE_UNSUPPORTED` and escalated for manual review. Zero assignments
  is the *correct* output here, not a shortfall.

**Validation, three unit tests plus one full end-to-end run — not a syntax
check on the generated XDC:**

- **Test A** (baseline checkpoint, no share-separation XDC, 1
  `MIXED_SITE_CONFLICT` site, 10 cells): 0 assignments, all 10 cells
  `NONE_UNSUPPORTED`. Confirms the refusal path fires and stays silent rather
  than guessing.
- **Test B** (v1 checkpoint, original hand-written XDC, the actual bug):
  2 assignments — `u_and_cross01/y_INST_0` -> sh1 via
  `SITE_UNANIMOUS_INFERENCE`, `u_and_cross10/y_INST_0` -> sh0 via
  `EXPLICIT_POLICY`. Both traceable in the generation log with cell, site,
  rule, and reason.
- **Test C** (v2 checkpoint, manually repaired reference XDC, already clean):
  0 assignments, explicit no-op XDC, empty generation log. Confirms the
  generator doesn't manufacture spurious constraints when there's nothing to
  fix.
- **End-to-end acceptance:** Test B's generated repair
  (`generated_repair_v1.xdc`) was concatenated *after the original broken*
  `share_separation.xdc` — not the hand-repaired v2 — into
  `share_separation_auto_repaired.xdc`, run from scratch through synthesis ->
  `opt_design` -> `place_design` -> `route_design`, and the resulting
  `post_route.dcp` was re-run through the *same frozen classifier* used for
  Tests A/B/C. Result: `0 MIXED_SITE_CONFLICT / 0 UNCLASSIFIED_CELL_PRESENT /
  0 UNCLASSIFIED_ONLY / 0 unclassified cells` — matching the manually repaired
  v2 ground truth exactly.

**Observed, disclosed anomaly:** applying the concatenated auto-repair XDC
produced `CRITICAL WARNING: [Place 30-8520] Ranges extend outside of device:
SLICE_X90Y99:SLICE_X60Y0` (`vivado_1288.backup.log`, line 56) — `pblock_share1`'s
range, inherited unchanged from the original `share_separation.xdc`, extends
outside `xc7a100tcsg324-1`'s real coordinate bounds. Vivado auto-clipped to
tile boundaries (`[Place 30-8517]`, same log, line 55) and placement/routing
completed successfully; final reclassification still shows 0/0/0/0. This is a
pre-existing property of the original XDC's own pblock range choice, not
something the generator introduced, and the automation does not "resolve" it —
it's carried through unchanged. Recorded here so it isn't rediscovered as a new
bug later.

**Decision:** accept the automated loop as validated for this one design and
this one conflict scenario. `MIXED_SITE_CONFLICT` remains permanently
unsupported for automatic repair by design, not as a temporary gap — the
correct behavior for a placement collision is human review, and the generator
change that would be needed to "resolve" one (moving a cell) is out of scope
for a pblock-membership generator by construction. Multi-gadget/multi-design
generalization was not attempted and is not claimed.
