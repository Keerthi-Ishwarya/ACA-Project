import csv, os, re
from metrics import ipcs, metrics, llc_evictions, dram_stats

D = "results_ckpt2"
SETUPS = ["baseline", "spp_fixed", "spp", "spp_bandpass"]

def done(p):
    return os.path.exists(p) and "Region of Interest Statistics" in open(p).read()

def mpki(p):
    m = re.search(r"LLC TOTAL.*MPKI:\s*([\d.]+)", open(p).read())
    return float(m.group(1)) if m else float("nan")

labels = [l.split()[0] for l in open("traces.txt") if l.strip()]
mixes = []
if os.path.exists("mixes2.txt"):
    mixes = [l.split() for l in open("mixes2.txt") if l.strip()]

print("Alone runs. gain = IPC setup / IPC baseline")
header = f"{'trace':10s}" + "".join(f"{('IPC ' + s):>16s}" for s in SETUPS) + f"{'LLC MPKI':>10s}"
print(header)
alone = {s: {} for s in SETUPS}
for lab in labels:
    row = []
    for s in SETUPS:
        p = f"{D}/alone_{s}_{lab}.txt"
        if done(p):
            alone[s][lab] = ipcs(p)[0]
        row.append(alone[s].get(lab))
    if any(v is not None for v in row):
        pm = f"{D}/alone_baseline_{lab}.txt"
        row_str = f"{lab:10s}"
        for v in row:
            row_str += f"{v:16.3f}" if v is not None else f"{'--':>16s}"
        row_str += f"{mpki(pm):10.2f}"
        print(row_str)
    else:
        print(f"{lab:10s} not finished")

KEYS = ["max_slowdown", "unfairness", "weighted_speedup", "harmonic_speedup"]
rows = []
if mixes:
    print("\nMixes: max slowdown, unfairness, weighted speedup, harmonic speedup")
for s in SETUPS:
    for i, mix in enumerate(mixes, 1):
        p = f"{D}/mix{i}_{s}.txt"
        if not done(p) or any(t not in alone[s] for t in mix):
            continue
        m = metrics(ipcs(p), [alone[s][t] for t in mix])
        vals = [round(m[k], 3) for k in KEYS]
        rows.append([s, i, " ".join(mix)] + vals)
        print(f"{s:14s} mix{i:<3d} {' '.join(mix):28s} {vals}")

with open("results_table_ckpt2.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["setup", "mix", "traces"] + KEYS)
    w.writerows(rows)