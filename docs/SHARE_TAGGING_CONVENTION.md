# Share Tagging Convention (v1)

Status: **Active** — governs all RTL written from Milestone 0 onward.
Supersedes: nothing (first formal version; Milestone 0 used this
implicitly, without writing it down, which is what this document fixes).

---

## Why this document exists

Milestone 0's coverage script (`milestone0_coverage.py`) determines which
physical FPGA resource belongs to which masking share by **pattern-matching
on signal/register names** (`infer_shares_heuristic()`). This worked, but
only because the RTL happened to be named consistently enough to match —
and the first Milestone 0 run (26.67% coverage) failed specifically
*because* naming wasn't consistent. The bug was fixed by hand-editing the
RTL to match the heuristic, not by fixing the heuristic itself.

This document makes the naming rule an explicit, written contract instead
of an implicit assumption living only inside one Python function. Every
future gadget's RTL must follow this convention. If the convention can't
express something (e.g. a signal that's neither share-specific nor
cross-share nor randomness), that's a signal this document needs a v2 —
not a reason to quietly special-case it in the parsing script.

**This is explicitly the "perimeter" version of M2**, not the "real"
metadata-driven Share Correlator described in Phase 12/13 of the frozen
project plan. It is a formalized heuristic, not a replacement for one. Any
report or write-up based on this convention must state that plainly as a
scope limitation (see "Known Limitations" below) — this is the honest
framing agreed on for the semester-scoped version of the project.

---

## The rule

Every signal or register in masked-gadget RTL must fall into exactly one
of these four categories, identified by a substring in its name:

| Category | Required substring | Meaning |
|---|---|---|
| Share 0 | `_sh0` | Carries only share-0 data |
| Share 1 | `_sh1` | Carries only share-1 data |
| Cross-share | `_cross` | Legitimately combines both shares (e.g. a DOM-style cross-domain AND term) |
| Randomness | `_r` (as a standalone suffix, e.g. `_r`, `_r_reg`) | Fresh mask/randomness input, not a share of any secret value |

Anything that doesn't fall into one of these four categories (e.g. plain
control logic, clock, reset, unrelated glue signals) is intentionally left
**untagged**, and the coverage script must treat "untagged and structurally
irrelevant" as a distinct outcome from "untagged and should have been
tagged but wasn't" — see Decision 10's `r_r_reg` case for the precedent:
it was correctly untagged because it is randomness, not a share.

### Naming examples (from Milestone 0, retroactively conforming)

- `a_sh1_r_reg` — share 1 of signal `a`. (Note: contains both `_sh1` and
  `_r` — see Ambiguity Rule below for how the script must resolve this.)
- `b_sh0_r_reg` — share 0 of signal `b`.
- `u_and_cross10/y_INST_0` — a cross-share AND term (produces a term mixing
  share 1 and share 0). Reported by the coverage script as `share = "0,1"`.
- `r_r_reg` — fresh mask randomness. No share substring. Correctly
  unmapped.
- `q_sh0_reg_reg` — share 0 of the output register `q`.

### Ambiguity Rule

If a signal name contains **both** a share substring (`_sh0`/`_sh1`) and
`_r`, the share substring wins — it is classified by share, not as
randomness. `_r` alone (with no `_sh0`/`_sh1` substring anywhere in the
name) is the only pattern that means "randomness." This is exactly the
resolution already implicit in how Milestone 0's `a_sh1_r_reg` was
correctly classified as share 1, not randomness — this section just makes
that resolution explicit and intentional rather than accidental.

### What caused the Milestone 0 bug, and how this rule prevents recurrence

The first Milestone 0 run (26.67% coverage) failed because some test
instrumentation registers used a bare-digit convention (e.g. something
like `sig0`/`sig1`) instead of the `_sh0`/`_sh1` substring the heuristic
matched on. Under this convention, **`_sh0`/`_sh1` are the only valid
share markers** — bare digits, `s0`/`s1`, `share0`/`share1`, or any other
variant are non-conforming and must be renamed before synthesis, not
accommodated by loosening the parser's regex. Loosening the parser to
catch more variants is exactly the kind of "gaming the measurement instead
of fixing the RTL" move the project's own guide warns against (Stage 1,
step 7 note; Stage 2's Branch A/B/C framing depends on this discipline).

---

## Required RTL comment header

Every masked gadget file must start with a header block stating its share
count and which signals are its top-level share inputs/outputs, so a
human reviewer (or a future automated tool) doesn't have to infer this
from scratch:

```verilog
// SHARE_TAGGING_CONVENTION v1
// Shares: 2
// Inputs:  a_sh0, a_sh1, b_sh0, b_sh1
// Outputs: q_sh0, q_sh1
// Randomness: r_r
```

This header is documentation only — the coverage script does not parse it
in v1. It exists so that manual inspection (Stage 1, step 7) has a ground
truth to check the automated mapping against, independent of the naming
heuristic itself.

---

## Known Limitations (state these explicitly in any write-up)

1. **This is a naming convention, not a semantic guarantee.** Nothing
   prevents a signal from being named `x_sh0` while actually containing
   share-1 data due to a copy-paste error. The convention only helps if
   RTL authors follow it correctly — Milestone 0's own bug is proof this
   isn't self-enforcing.
2. **It does not survive renaming by synthesis tools.** If a future
   Vivado version or optimization pass renames internal nets, coverage
   could drop for reasons unrelated to actual share-separation — this is
   exactly the class of failure Stage 1, step 4 (skimming DRC/timing
   reports) exists to catch.
3. **This is explicitly not the "real" M2 mechanism** described in the
   original frozen project plan (RTL-metadata-driven correlation,
   independent of naming). That remains future work. This convention is
   the documented, defensible heuristic used for the semester-scoped
   deliverable.

---

## Change Log

- **v1 (this version):** Initial formalization, written after Milestone 0
  completion (93.33% coverage, Decision 10). Codifies the `_sh0`/`_sh1`/
  `_cross`/`_r` convention already used implicitly in
  `masked_and_gadget.v`.
