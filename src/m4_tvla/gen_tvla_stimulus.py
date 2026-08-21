#!/usr/bin/env python3
"""
gen_tvla_stimulus.py -- generates stimulus.mem for the TVLA testbench,
using numpy's PCG64 generator instead of Vivado xsim's $urandom.

WHY THIS EXISTS: three rounds of testbench fixes (seeding, then matching
RNG call-counts between populations) failed to make the term_cross01
"leak" go away -- it got STRONGER after the call-count fix (-3.752 to
-7.850). That ruled out unequal call counts as the cause. The remaining
explanation: population 0's "b_sh1 = b_sh0" construction means
term_cross01 (a_sh0 & b_sh1) ANDs together RNG-stream positions 1 and 3,
while population 1's term_cross01 ANDs positions 1 and 4 -- genuinely
different pairs of stream positions. Vivado's $urandom_range(0,1) very
likely extracts the low bit of a simple LCG, and LCG low bits are the
textbook-weakest, most serially-correlated part of any LCG's output.
No amount of reordering calls inside the testbench closes this off,
because the confound is baked into which specific positions get
combined, not how many calls happen.

This script sidesteps the whole problem: generate all stimulus with a
real PRNG (PCG64, no known low-bit correlation) OUTSIDE the simulator,
write it to a file, and have the testbench just read rows sequentially.
There is no in-simulator call-ordering left to get wrong.

Output: stimulus.mem -- one 6-bit binary value per line, for $readmemb.
    Bit layout (MSB to LSB): [population][a_sh0][a_sh1][b_sh0][b_sh1][r]

USAGE:
    python gen_tvla_stimulus.py --n-per-population 20000 --seed 42 --out stimulus.mem
"""

import argparse
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n-per-population", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="stimulus.mem")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    n = args.n_per_population

    lines = []

    # Population 0 (fixed): logical a=0, b=0.
    # a_sh0 fresh uniform random, a_sh1 = a_sh0 (so a_sh0 XOR a_sh1 = 0).
    # b_sh0 fresh uniform random, b_sh1 = b_sh0 (so b_sh0 XOR b_sh1 = 0).
    a_sh0_0 = rng.integers(0, 2, size=n)
    b_sh0_0 = rng.integers(0, 2, size=n)
    r_0 = rng.integers(0, 2, size=n)
    for i in range(n):
        a0, b0, ri = a_sh0_0[i], b_sh0_0[i], r_0[i]
        a1 = a0  # a_sh1 = a_sh0
        b1 = b0  # b_sh1 = b_sh0
        bits = f"0{a0}{a1}{b0}{b1}{ri}"
        lines.append(bits)

    # Population 1 (random): a, b independently randomized.
    a_sh0_1 = rng.integers(0, 2, size=n)
    a_sh1_1 = rng.integers(0, 2, size=n)
    b_sh0_1 = rng.integers(0, 2, size=n)
    b_sh1_1 = rng.integers(0, 2, size=n)
    r_1 = rng.integers(0, 2, size=n)
    for i in range(n):
        bits = f"1{a_sh0_1[i]}{a_sh1_1[i]}{b_sh0_1[i]}{b_sh1_1[i]}{r_1[i]}"
        lines.append(bits)

    with open(args.out, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote {len(lines)} stimulus rows to {args.out}")
    print(f"  population 0 (fixed):  rows 0..{n-1}")
    print(f"  population 1 (random): rows {n}..{2*n-1}")
    print(f"  seed: {args.seed}")

    # Quick sanity check: confirm the generator itself has no detectable
    # correlation between the specific column pairs that flagged as
    # "leaks" before, since if numpy also showed this, the theory would
    # be wrong and something else would need investigating.
    from scipy import stats
    pop0_cross01 = (a_sh0_0 & b_sh0_0)  # b_sh1=b_sh0 in pop0
    pop1_cross01 = (a_sh0_1 & b_sh1_1)
    t, p = stats.ttest_ind(pop0_cross01.astype(float), pop1_cross01.astype(float), equal_var=False)
    print(f"\nSanity check -- t-test on the generator's own term_cross01-equivalent bits:")
    print(f"  t = {t:.3f}, p = {p:.3e}  (should be small/insignificant if PCG64 has no low-bit correlation issue)")


if __name__ == "__main__":
    main()
