#!/usr/bin/env python3
import argparse
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-per-population", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="stimulus_v2_fixed11.mem")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    n = args.n_per_population
    lines = []

    # Population 0 (fixed): logical a=1, b=1.
    # a_sh1 = NOT a_sh0 (so a_sh0 XOR a_sh1 = 1), b_sh1 = NOT b_sh0 likewise.
    # This avoids the a=0,b=0 degenerate collapse where all four AND-gadget
    # product terms become forced-identical.
    a_sh0_0 = rng.integers(0, 2, size=n)
    b_sh0_0 = rng.integers(0, 2, size=n)
    r_0 = rng.integers(0, 2, size=n)
    for i in range(n):
        a0, b0, ri = a_sh0_0[i], b_sh0_0[i], r_0[i]
        a1 = 1 - a0
        b1 = 1 - b0
        bits = f"0{a0}{a1}{b0}{b1}{ri}"
        lines.append(bits)

    # Population 1 (random): unchanged, a and b independently randomized.
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
    print(f"  population 0 (fixed, a=1 b=1): rows 0..{n-1}")
    print(f"  population 1 (random):         rows {n}..{2*n-1}")
    print(f"  seed: {args.seed}")

if __name__ == "__main__":
    main()
