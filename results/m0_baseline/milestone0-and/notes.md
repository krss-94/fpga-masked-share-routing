\# Milestone 0 — Toy 2-Share AND Gadget



\## Result

Coverage: 93.33% (14/15 logical cells mapped)

\- 0 ambiguous

\- 1 correctly unmapped (r\_r\_reg — fresh randomness register, not a share)



Initial run showed 26.67% coverage due to an inconsistent naming

convention in RTL test instrumentation (some registers used a bare-digit

convention instead of the sh0/sh1 substring the heuristic matched on).

Caught during manual inspection of coverage.csv, fixed at the RTL level.



\## Decision

Proceed to Stage 3 (Branch A — coverage high, mapping mechanism sound).

