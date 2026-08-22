#!/usr/bin/env python3
import sys, csv, argparse, itertools
from collections import defaultdict
try:
    import numpy as np
    from scipy import stats
except ImportError:
    print("Missing dependency. Install with:")
    print("  pip install numpy scipy")
    sys.exit(1)

PRIORITY_PAIRS = [
    ("a_sh0_r", "a_sh1_r"),
    ("b_sh0_r", "b_sh1_r"),
    ("term_cross01", "term_cross10"),
    ("t0_sh0", "t0_sh1"),
    ("term_sh0", "term_sh1"),
]

def load_trace(csv_path):
    data = {0: defaultdict(list), 1: defaultdict(list)}
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        columns = [c for c in reader.fieldnames if c not in ("population", "cycle", "hamming_weight")]
        for row in reader:
            pop = int(row["population"])
            for col in columns:
                data[pop][col].append(int(row[col]))
    return data, columns

def centered_product_series(data, pop, colx, coly):
    x = np.array(data[pop][colx], dtype=float)
    y = np.array(data[pop][coly], dtype=float)
    return (x - x.mean()) * (y - y.mean())

def welch_t(a, b):
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return t, p

def run_pair(data, colx, coly, threshold):
    c0 = centered_product_series(data, 0, colx, coly)
    c1 = centered_product_series(data, 1, colx, coly)
    t, p = welch_t(c0, c1)
    leaked = abs(t) > threshold
    return t, p, leaked

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv")
    parser.add_argument("--threshold", type=float, default=4.5)
    parser.add_argument("--full-sweep", action="store_true")
    args = parser.parse_args()

    data, columns = load_trace(args.csv)
    n0 = len(data[0][columns[0]])
    n1 = len(data[1][columns[0]])
    print(f"Loaded trace: population 0 (fixed) = {n0} samples, population 1 (random) = {n1} samples")
    print(f"Signal columns available: {columns}\n")

    print("=== PRIORITY PAIRS (security-relevant: same-secret shares, cross terms, output sums) ===")
    print(f"{'pair':<32} {'t-statistic':>12} {'p-value':>12} {'verdict':>10}")
    print("-" * 70)
    worst = None
    for colx, coly in PRIORITY_PAIRS:
        if colx not in columns or coly not in columns:
            print(f"{colx+'/'+coly:<32} SKIPPED (column not present in this trace)")
            continue
        t, p, leaked = run_pair(data, colx, coly, args.threshold)
        verdict = "LEAK" if leaked else "ok"
        print(f"{colx+'/'+coly:<32} {t:>12.3f} {p:>12.2e} {verdict:>10}")
        if worst is None or abs(t) > abs(worst[2]):
            worst = (colx, coly, t)

    if args.full_sweep:
        print("\n=== FULL SWEEP: all pairwise combinations ===")
        print(f"{'pair':<32} {'t-statistic':>12} {'p-value':>12} {'verdict':>10}")
        print("-" * 70)
        for colx, coly in itertools.combinations(columns, 2):
            t, p, leaked = run_pair(data, colx, coly, args.threshold)
            verdict = "LEAK" if leaked else "ok"
            print(f"{colx+'/'+coly:<32} {t:>12.3f} {p:>12.2e} {verdict:>10}")
            if abs(t) > abs(worst[2]):
                worst = (colx, coly, t)

    print(f"\nWorst-case pair: {worst[0]}/{worst[1]} at |t| = {abs(worst[2]):.3f} (threshold {args.threshold})")
    if abs(worst[2]) > args.threshold:
        print(f"\n>>> 2ND-ORDER TVLA FLAGS JOINT LEAKAGE (simulated proxy) <<<")
        print(f"The pair {worst[0]}/{worst[1]} shows a population-dependent covariance structure")
        print(f"that neither signal's marginal (1st-order) test alone would catch.")
    else:
        print(f"\nNo tested pair exceeds the threshold in this simulated proxy.")
        print(f"This is evidence AGAINST simple 2nd-order structure between these signal pairs")
        print(f"in the Hamming-weight proxy model -- it is not a proof of physical resistance to")
        print(f"a real 2nd-order power/EM attack, and this design was never claimed to be")
        print(f"2nd-order secure (single fresh mask bit = 1st-order masking scheme).")

if __name__ == "__main__":
    main()
