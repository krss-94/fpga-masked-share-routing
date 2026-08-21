\# Gadget #2 — Masked XOR



\## Result

Coverage: 80.00% (16/20 total objects mapped)

\- 0 ambiguous

\- 4 unmapped, all correctly excluded: clk, clk\_IBUF\_inst,

&#x20; clk\_IBUF\_BUFG\_inst, <LOCKED> — clock/implementation infrastructure,

&#x20; not share-bearing objects (a/b/q).



Of the 16 mapped objects (the actual gadget logic), 100% resolved to

exactly one share (0 or 1) with zero cross-share terms — consistent with

XOR being a linear operation requiring no randomness and no cross-share

mixing, unlike the AND gadget (Milestone 0) which needed a cross-share

term. Shares stayed fully separated through synthesis, placement, and

routing.



\## Decision

Accept mapping strategy for this gadget (Branch A). Coverage on

share-bearing objects specifically is effectively 100% (16/16) once

clock infrastructure is excluded — the 80% aggregate figure understates

true coverage because it counts non-share objects as a fixed denominator,

same category of finding as Milestone 0's r\_r\_reg.

