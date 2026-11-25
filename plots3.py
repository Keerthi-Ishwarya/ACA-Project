#!/usr/bin/env python3

import csv, math, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "results_ckpt2"
SETUPS = ["baseline", "spp_fixed", "spp", "spp_bandpass"]
COLORS = {"baseline": "#999999", "spp_fixed": "#1f77b4", "spp": "#2ca02c", "spp_bandpass": "#d62728"}

# ------------------------------------------------------------ load csv
data = {s: {} for s in SETUPS}
names = {}
with open("results_summary.csv") as f:
    for r in csv.DictReader(f):
        k = int(r["mix"])
        names[k] = r["mixname"]
        data[r["setup"]][k] = {c: float(v) for c, v in r.items() if c not in ("setup", "mix", "mixname")}
mixes = sorted(names)
hetero = [k for k in mixes if len(set(names[k].split("+"))) > 1]


def gmean(x):
    return math.exp(sum(math.log(v) for v in x) / len(x))


# ------------------------------------------------------------ fig 1: summary bars
fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
for a, (key, title) in zip(ax, (("maxsd_base", "Max slowdown (lower is better)"),
                                 ("unf_base", "Unfairness (1 = equal)"),
                                 ("hs_base", "Harmonic speedup (higher is better)"))):
    vals = [gmean([data[s][k][key] for k in hetero]) for s in SETUPS]
    a.bar(range(4), vals, color=[COLORS[s] for s in SETUPS])
    for i, v in enumerate(vals):
        a.text(i, v, f"{v:.3f}", ha="center", va="bottom", fontsize=8)
    a.set_xticks(range(4))
    a.set_xticklabels(SETUPS, rotation=20, fontsize=8)
    a.set_title(title, fontsize=10)
    lo = min(vals)
    a.set_ylim(min(lo * 0.85, lo - 0.05), max(vals) * 1.08)
fig.suptitle("Mixed (heterogeneous) mixes, geometric mean, reference = baseline alone IPC", fontsize=10)
plt.tight_layout()
plt.savefig("fig1_summary.png", dpi=150)
plt.close()

# ------------------------------------------------------------ fig 2: unfairness per mix
fig, a = plt.subplots(figsize=(13, 4))
w = 0.2
for i, s in enumerate(SETUPS):
    a.bar([k + (i - 1.5) * w for k in mixes], [data[s][k]["unf_base"] for k in mixes],
          width=w, label=s, color=COLORS[s])
a.set_xticks(mixes)
a.set_xticklabels([f"{k}\n{names[k].replace('+', ',')[:14]}" for k in mixes], fontsize=6)
a.set_ylabel("Unfairness (largest / smallest slowdown)")
a.set_title("Unfairness per mix (reference = baseline alone IPC)", fontsize=10)
a.legend(fontsize=8)
plt.tight_layout()
plt.savefig("fig2_unfairness_per_mix.png", dpi=150)
plt.close()

# ------------------------------------------------------------ fig 3: bandpass vs spp_fixed
fig, ax = plt.subplots(1, 2, figsize=(13, 3.8))
d_hs = [(data["spp_bandpass"][k]["hs_base"] / data["spp_fixed"][k]["hs_base"] - 1) * 100 for k in mixes]
d_un = [(data["spp_bandpass"][k]["unf_base"] / data["spp_fixed"][k]["unf_base"] - 1) * 100 for k in mixes]
for a, vals, title in ((ax[0], d_hs, "Harmonic speedup change (%)  (+ is better)"),
                       (ax[1], d_un, "Unfairness change (%)  (- is better)")):
    a.bar(mixes, vals, color=["#d62728" if (v < 0) == (a is ax[0]) else "#2ca02c" for v in vals])
    a.axhline(0, color="black", lw=0.8)
    a.axhspan(-0.5, 0.5, color="grey", alpha=0.2)
    a.set_xticks(mixes)
    a.set_xticklabels(mixes, fontsize=8)
    a.set_xlabel("mix number")
    a.set_title("Band-Pass vs spp_fixed: " + title, fontsize=9)
plt.tight_layout()
plt.savefig("fig3_bandpass_vs_fixed.png", dpi=150)
plt.close()

# ------------------------------------------------------------ fig 4: PF vs accuracy
BPRE = re.compile(r"CPU (\d+) BP-SPP Final Stats: Degree=\d+ Demands=\d+ Prefetches=\d+ "
                  r"Prefetch_Fraction=(\S+) Useful=\d+ Accuracy=(\S+)")
mix_labels = [l.split() for l in open("mixes2.txt").read().replace("\r", "").splitlines() if l.strip()]
pts = []
for k in mixes:
    try:
        t = open(f"{R}/mix{k}_spp_bandpass.txt", errors="ignore").read()
    except OSError:
        continue
    seen = {}
    for m in BPRE.finditer(t):
        seen[int(m.group(1))] = (float(m.group(2)), float(m.group(3)))
    for i, (pf, acc) in seen.items():
        pts.append((mix_labels[k - 1][i], pf, acc))
labs = sorted(set(p[0] for p in pts))
cmap = plt.get_cmap("tab10")
fig, a = plt.subplots(figsize=(6.5, 5))
for j, lb in enumerate(labs):
    xs = [p[1] for p in pts if p[0] == lb]
    ys = [p[2] for p in pts if p[0] == lb]
    a.scatter(xs, ys, label=lb, color=cmap(j % 10), s=28, alpha=0.8)
a.set_xlabel("Prefetch fraction (printed in final stats, all L1D accesses)")
a.set_ylabel("Prefetch accuracy (lower bound, 256-entry buffer)")
a.set_title("Does prefetch fraction follow accuracy?\n(paper: yes, rho~0.76;  here: rho=-0.30)", fontsize=10)
a.set_xlim(left=0)
a.set_ylim(0, 1)
a.legend(fontsize=7, ncol=2)
plt.tight_layout()
plt.savefig("fig4_pf_vs_accuracy.png", dpi=150)
plt.close()

print("wrote fig1_summary.png, fig2_unfairness_per_mix.png, fig3_bandpass_vs_fixed.png, fig4_pf_vs_accuracy.png")