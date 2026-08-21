#!/usr/bin/env python3
"""
tvla_analysis.py -- computes the actual TVLA statistic (Welch's t-test)
on the Hamming-weight leakage-proxy trace produced by
tb_masked_and_gadget_tvla.v.

Standard TVLA convention: |t| > 4.5 anywhere is treated as detectable
leakage (roughly a 0.9999995 confidence threshold, per Goodwill et al.'s
original TVLA methodology). This script reports the max |t|, where it
occurs, and which raw signal(s) (not just the combined Hamming weight)
are driving it, so a "leak" isn't just a single opaque number.

REMINDER: this is leakage in a simulated Hamming-weight proxy, not a
measured leak on real silicon. Report it as such.

USAGE:
    python tvla_analysis.py tvla_trace.csv
"""

import sys
import csv
import argparse
from collections import defaultdict

try:
    import numpy as np
    from scipy import stats
except ImportError:
    print("Missing dependency. Install with:")
    print("  pip install numpy scipy")
    sys.exit(1)


def load_trace(csv_path):
    """Returns dict: {population: {column_name: [values...]}}"""
    data = {0: defaultdict(list), 1: defaultdict(list)}
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        columns = [c for c in reader.fieldnames if c not in ("population", "cycle")]
        for row in reader:
            pop = int(row["population"])
            for col in columns:
                data[pop][col].append(int(row[col]))
    return data, columns


def welch_t_test(pop0_vals, pop1_vals):
    """Returns (t_statistic, p_value). Welch's t-test -- does not assume
    equal variance between populations, which is the correct test for
    TVLA (the two populations have no reason to share variance)."""
    a = np.array(pop0_vals, dtype=float)
    b = np.array(pop1_vals, dtype=float)
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return t, p


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", help="tvla_trace.csv from the testbench")
    parser.add_argument("--threshold", type=float, default=4.5,
                         help="TVLA |t| threshold for a leak flag (default 4.5, standard TVLA convention)")
    args = parser.parse_args()

    data, columns = load_trace(args.csv)

    n0 = len(data[0]["hamming_weight"])
    n1 = len(data[1]["hamming_weight"])
    print(f"Loaded trace: population 0 (fixed) = {n0} samples, population 1 (random) = {n1} samples\n")

    if n0 == 0 or n1 == 0:
        print("ERROR: one population has zero samples -- check the CSV / testbench population labeling.")
        sys.exit(1)

    print(f"{'signal':<16} {'t-statistic':>12} {'p-value':>12} {'verdict':>10}")
    print("-" * 54)

    results = []
    for col in columns:
        t, p = welch_t_test(data[0][col], data[1][col])
        leaked = abs(t) > args.threshold
        results.append((col, t, p, leaked))
        verdict = "LEAK" if leaked else "ok"
        print(f"{col:<16} {t:>12.3f} {p:>12.2e} {verdict:>10}")

    print()
    worst = max(results, key=lambda r: abs(r[1]))
    print(f"Worst-case: '{worst[0]}' at |t| = {abs(worst[1]):.3f} "
          f"(threshold {args.threshold})")

    if abs(worst[1]) > args.threshold:
        print(f"\n>>> TVLA FLAGS LEAKAGE (simulated Hamming-weight proxy, not physical measurement) <<<")
        print(f"Signal '{worst[0]}' distinguishes the two populations with high confidence.")
        print(f"This means the gadget's simulated switching activity for this signal statistically")
        print(f"correlates with whether the logical secret is fixed or random -- exactly the pattern")
        print(f"a real side-channel attacker would exploit, IF this proxy reflects real power draw.")
    else:
        print(f"\nNo signal exceeds the TVLA threshold in this simulated proxy.")
        print(f"This does NOT prove the physical implementation is leak-free -- it only means the")
        print(f"logical/behavioral simulation shows no detectable first-order Hamming-weight leakage.")
        print(f"Routing-induced coupling (the switchbox_conflict_detector.py findings) operates at a")
        print(f"physical layer this simulation cannot see.")


if __name__ == "__main__":
    main()
