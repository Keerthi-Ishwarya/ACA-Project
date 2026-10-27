import os, csv
from metrics import ipcs, metrics

def done(p):
    return os.path.exists(p) and "Region of Interest Statistics" in open(p).read()

mixes = [l.split() for l in open("mixes.txt") if l.strip()]
rows = []
for setup in ["baseline", "spp", "spp_fixed"]:
    alone = {}
    for t in ["T1", "T2", "T3"]:
        p = f"results/alone_{setup}_{t}.txt"
        if done(p):
            alone[t] = ipcs(p)[0]
    for i, mix in enumerate(mixes, 1):
        p = f"results/mix{i}_{setup}.txt"
        if not done(p) or any(t not in alone for t in mix):
            print(f"{setup:10s} mix{i}: not finished yet")
            continue
        shared = ipcs(p)
        m = metrics(shared, [alone[t] for t in mix])
        rows.append([setup, i, " ".join(mix)] + [round(m[k], 3) for k in
                    ["max_slowdown", "unfairness", "weighted_speedup", "harmonic_speedup"]])
        print(setup, i, " ".join(mix), [round(x, 3) for x in rows[-1][3:]])

with open("results_table.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["setup", "mix", "traces", "max_slowdown", "unfairness",
                "weighted_speedup", "harmonic_speedup"])
    w.writerows(rows)
