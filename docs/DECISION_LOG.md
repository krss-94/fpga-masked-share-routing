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

