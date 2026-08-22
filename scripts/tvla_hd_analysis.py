#!/usr/bin/env python3
import sys, csv, argparse
from collections import defaultdict
try:
    import numpy as np
    from scipy import stats
except ImportError:
    print("Missing dependency. Install with:")
    print("  pip install numpy scipy")
    sys.exit(1)

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

def hd_series(values):
    arr = np.array(values, dtype=int)
    return np.abs(np.diff(arr))

def welch_t(a, b):
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return t, p

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv")
    parser.add_argument("--threshold", type=float, default=4.5)
    args = parser.parse_args()

    data, columns = load_trace(args.csv)
    n0 = len(data[0][columns[0]])
    n1 = len(data[1][columns[0]])
    print(f"Loaded trace: population 0 (fixed) = {n0} samples, population 1 (random) = {n1} samples")
    print(f"Signal columns available: {columns}\n")

    print(f"{'signal (HD)':<20} {'t-statistic':>12} {'p-value':>12} {'verdict':>10}")
    print("-" * 58)

    hd0_matrix = []
    hd1_matrix = []
    worst = None
    for col in columns:
        hd0 = hd_series(data[0][col])
        hd1 = hd_series(data[1][col])
        hd0_matrix.append(hd0)
        hd1_matrix.append(hd1)
        t, p = welch_t(hd0, hd1)
        leaked = abs(t) > args.threshold
        verdict = "LEAK" if leaked else "ok"
        print(f"{col:<20} {t:>12.3f} {p:>12.2e} {verdict:>10}")
        if worst is None or abs(t) > abs(worst[1]):
            worst = (col, t)

    combined_hd0 = np.sum(np.array(hd0_matrix), axis=0)
    combined_hd1 = np.sum(np.array(hd1_matrix), axis=0)
    t, p = welch_t(combined_hd0, combined_hd1)
    leaked = abs(t) > args.threshold
    verdict = "LEAK" if leaked else "ok"
    print(f"{'combined_toggle_hd':<20} {t:>12.3f} {p:>12.2e} {verdict:>10}")
    if abs(t) > abs(worst[1]):
        worst = ("combined_toggle_hd", t)

    print(f"\nWorst-case: '{worst[0]}' at |t| = {abs(worst[1]):.3f} (threshold {args.threshold})")
    if abs(worst[1]) > args.threshold:
        print(f"\n>>> HAMMING-DISTANCE TVLA FLAGS LEAKAGE (simulated proxy) <<<")
        print(f"Signal/combined metric '{worst[0]}' shows population-dependent switching activity.")
    else:
        print(f"\nNo signal or combined toggle metric exceeds the threshold.")
        print(f"This is a second, independent leakage model (transition-based) showing no detectable")
        print(f"difference, complementing the existing static Hamming-Weight result -- still only a")
        print(f"statement about this simulated proxy, not a physical measurement.")

if __name__ == "__main__":
    main()
