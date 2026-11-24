#!/usr/bin/env python3

import math
import os
import re

import matplotlib
matplotlib.use("Agg")                      # draw to files, no window needed
import matplotlib.pyplot as plt

from metrics import ipcs, metrics        

TRACES = ["T1", "T2", "T3"]
# (name used in the result file names, label in the figures, bar colour, bar hatch)
SETUPS = [
    ("baseline",  "No prefetcher",          "#bdbdbd", ""),
    ("spp_fixed", "Fixed degree 4",         "#0072B2", "//"),
    ("spp",       "Throttled degree 1-4",   "#E69F00", ".."),
]
TRACE_COLOURS = {"T1": "#0072B2", "T2": "#E69F00", "T3": "#009E73"}
OUT = "plots_slides"

plt.rcParams.update({"font.size": 17, "axes.titlesize": 18, "axes.labelsize": 17,
                     "legend.fontsize": 15, "figure.dpi": 100})


# ---------------------------------------------------------------- helpers
def geomean(values):
    return math.exp(sum(math.log(v) for v in values) / len(values))


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(f"{OUT}/{name}.png", dpi=200, bbox_inches="tight")
    fig.savefig(f"{OUT}/{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print("wrote", f"{OUT}/{name}.png")


def read_mixes():
    mixes = []
    for line in open("mixes.txt"):
        if line.strip():                    
            mixes.append(line.split())
    return mixes


def llc_mpki(path):
    """MPKI of the 'LLC TOTAL' line that ChampSim prints at the end of a run."""
    m = re.search(r"LLC TOTAL.*MPKI:\s*([\d.]+)", open(path).read())
    return float(m.group(1)) if m else None


def grouped_bar(ax, groups, series, ylabel, ymin=None, ymax=None, annotate=False, title=None):
    """series = list of (label, values, colour, hatch); one bar per series in every group."""
    n = len(series)
    width = 0.8 / n
    for j, (label, vals, colour, hatch) in enumerate(series):
        xs = [i - 0.4 + width * (j + 0.5) for i in range(len(groups))]
        ax.bar(xs, vals, width, label=label, color=colour, hatch=hatch,
               edgecolor="black", linewidth=0.6)
        if annotate:
            for x, v in zip(xs, vals):
                ax.text(x, v, f"{v:.2f}", ha="center", va="bottom", fontsize=11.05)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups, fontsize=13.6)
    ax.set_ylabel(ylabel)
    ax.set_ylim(bottom=ymin, top=ymax)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=n, frameon=False)



mixes = read_mixes()
labels = [f"M{i + 1}\n{''.join(m)}" for i, m in enumerate(mixes)]       
mixed = [i for i, m in enumerate(mixes) if len(set(m)) > 1]            

alone = {}      # alone[setup][trace] = IPC of the trace running alone
data = {}       # data[setup][mix index] = dict of the four metrics
core_sd = {}    # core_sd[setup][mix index] = slowdown of every core

for setup, _, _, _ in SETUPS:
    alone[setup] = {t: ipcs(f"results/alone_{setup}_{t}.txt")[0] for t in TRACES}
    data[setup], core_sd[setup] = [], []
    for i, mix in enumerate(mixes):
        shared = ipcs(f"results/mix{i + 1}_{setup}.txt")
        alone_ipcs = [alone[setup][t] for t in mix]
        data[setup].append(metrics(shared, alone_ipcs))
        core_sd[setup].append([a / s for a, s in zip(alone_ipcs, shared)])


def series_for(key, idx):
    return [(label, [data[s][i][key] for i in idx], colour, hatch)
            for s, label, colour, hatch in SETUPS]


all_idx = list(range(len(mixes)))

# ---------------------------------------------------------------- figure 1: unfairness
fig, ax = plt.subplots(figsize=(7, 3.6))
grouped_bar(ax, [labels[i] for i in mixed], series_for("unfairness", mixed),
            "Unfairness, largest / smallest slowdown\n(lower is better, 1 = fair)",
            ymin=1.0, annotate=True,
            title="Unfairness of the mixed workloads")
save(fig, "fig_unfairness")

# ---------------------------------------------------------------- figure 2: maximum slowdown
fig, ax = plt.subplots(figsize=(10, 3.6))
grouped_bar(ax, labels, series_for("max_slowdown", all_idx),
            "Maximum slowdown\n(lower is better)", ymin=1.0,
            title="Maximum slowdown (M1-M3: one trace on all four cores)")
save(fig, "fig_max_slowdown")

# ---------------------------------------------------------------- figure 3: weighted speedup
fig, ax = plt.subplots(figsize=(10, 3.6))
grouped_bar(ax, labels, series_for("weighted_speedup", all_idx),
            "Weighted speedup\n(higher is better, maximum 4)", ymin=0, ymax=4,
            title="Weighted speedup")
save(fig, "fig_weighted_speedup")

# ---------------------------------------------------------------- figure 4: harmonic speedup
fig, ax = plt.subplots(figsize=(10, 3.6))
grouped_bar(ax, labels, series_for("harmonic_speedup", all_idx),
            "Harmonic speedup\n(higher is better, maximum 1)", ymin=0, ymax=1,
            title="Harmonic speedup")
save(fig, "fig_harmonic_speedup")

# ---------------------------------------------------------------- figure 5: slowdown of every core
for setup, label, _, _ in SETUPS:
    fig, ax = plt.subplots(figsize=(10, 3.6))
    xs, heights, colours, ticks, tick_pos, mix_centres = [], [], [], [], [], []
    x = 0
    for i, mix in enumerate(mixes):
        start = x
        for t, sd in zip(mix, core_sd[setup][i]):
            xs.append(x)
            heights.append(sd)
            colours.append(TRACE_COLOURS[t])
            ticks.append(t)
            tick_pos.append(x)
            x += 1
        mix_centres.append((i, (start + x - 1) / 2))
        x += 1                                          # empty slot between mixes
    ax.bar(xs, heights, 0.8, color=colours, edgecolor="black", linewidth=0.6)
    ax.set_xticks(tick_pos)
    ax.set_xticklabels(ticks, fontsize=11.9)
    for i, centre in mix_centres:
        ax.text(centre, -0.16, f"M{i + 1}", ha="center", va="top", fontsize=15.3,
                transform=ax.get_xaxis_transform())
    ax.set_ylim(bottom=1.0)
    ax.set_ylabel("Slowdown of the core\n(lower is better)")
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    ax.set_title(f"Slowdown of every core, {label}")
    handles = [plt.Rectangle((0, 0), 1, 1, color=TRACE_COLOURS[t], ec="black") for t in TRACES]
    ax.legend(handles, [f"Core runs {t}" for t in TRACES], loc="upper center",
              bbox_to_anchor=(0.5, -0.28), ncol=3, frameon=False)
    save(fig, f"fig_core_slowdown_{setup}")

# ---------------------------------------------------------------- figure 6: alone IPC
fig, ax = plt.subplots(figsize=(6, 3.4))
series = [(label, [alone[s][t] for t in TRACES], colour, hatch)
          for s, label, colour, hatch in SETUPS]
grouped_bar(ax, TRACES, series, "IPC of the trace running alone\n(higher is better)",
            ymin=0, annotate=True, title="Alone IPC (one core, 8 MB LLC)")
save(fig, "fig_alone_ipc")

# ---------------------------------------------------------------- figure 7: LLC MPKI (no prefetcher)
mpki = {t: llc_mpki(f"results/alone_baseline_{t}.txt") for t in TRACES}
if all(v is not None for v in mpki.values()):
    fig, ax = plt.subplots(figsize=(4.2, 3.4))
    ax.bar(TRACES, [mpki[t] for t in TRACES], 0.55, color="#bdbdbd", edgecolor="black", linewidth=0.6)
    for k, t in enumerate(TRACES):
        ax.text(k, mpki[t], f"{mpki[t]:.2f}", ha="center", va="bottom", fontsize=13.6)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("LLC misses per kilo-instruction\n(lower is better)")
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    ax.set_title("LLC MPKI, trace alone, no prefetcher")
    save(fig, "fig_llc_mpki")
else:
    print("no 'LLC TOTAL ... MPKI' line found in the alone_baseline files, skipped fig_llc_mpki")

# ---------------------------------------------------------------- figure 8: geometric mean over the mixed workloads
panels = [("max_slowdown",     "Maximum slowdown\n(lower is better)",       1.0),
          ("unfairness",        "Unfairness\n(lower is better)",             1.0),
          ("weighted_speedup",  "Weighted speedup\n(higher is better)",      0.0),
          ("harmonic_speedup",  "Harmonic speedup\n(higher is better)",      0.0)]
fig, axes = plt.subplots(1, 4, figsize=(12, 3.4))
short = ["No\nprefetcher", "Fixed\ndegree 4", "Throttled\n1-4"]
summary = {}
for ax, (key, ylabel, ymin) in zip(axes, panels):
    vals = [geomean([data[s][i][key] for i in mixed]) for s, _, _, _ in SETUPS]
    summary[key] = vals
    ax.bar(range(3), vals, 0.6, color=[c for _, _, c, _ in SETUPS],
           hatch=None, edgecolor="black", linewidth=0.6)
    for k, v in enumerate(vals):
        ax.text(k, v, f"{v:.3f}", ha="center", va="bottom", fontsize=13.6)
    ax.set_xticks(range(3))
    ax.set_xticklabels(short, fontsize=13.6)
    ax.set_ylabel(ylabel)
    ax.set_ylim(bottom=ymin)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
fig.suptitle("Geometric mean over the mixed workloads", fontsize=17)
fig.tight_layout()
save(fig, "fig_geomean_mixed")

# ---------------------------------------------------------------- numbers to copy into the report
print("\nGeometric mean over the mixed workloads:", ", ".join(labels[i].split("\n")[0] for i in mixed))
print(f"{'setup':24s}{'max slowdown':>14s}{'unfairness':>12s}{'weighted':>10s}{'harmonic':>10s}")
for k, (s, label, _, _) in enumerate(SETUPS):
    print(f"{label:24s}{summary['max_slowdown'][k]:14.3f}{summary['unfairness'][k]:12.3f}"
          f"{summary['weighted_speedup'][k]:10.3f}{summary['harmonic_speedup'][k]:10.3f}")
print("\nLLC MPKI (alone, no prefetcher):", {t: (round(v, 3) if v else None) for t, v in mpki.items()})