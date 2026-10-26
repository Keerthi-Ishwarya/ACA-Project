import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "results"
os.makedirs(OUT, exist_ok=True)

traces   = ["Trace 1", "Trace 2", "Trace 3"]
policies = ["LRU", "RRIP", "I-RRIP"]
colors   = {"LRU": "#7f8c8d", "RRIP": "#3498db", "I-RRIP": "#e67e22"}

# Values copied from the six final logs (one entry per trace)
ipc = {"LRU":    [0.232204, 0.251130, 0.382061],
       "RRIP":   [0.232075, 0.251900, 0.381743],
       "I-RRIP": [0.232104, 0.256164, 0.381987]}
l2c = {"LRU":    [17.7302, 27.9234, 3.95904],
       "RRIP":   [17.6155, 26.2957, 4.04324],
       "I-RRIP": [17.6440, 23.1610, 3.90752]}
l2i = {"LRU":    [10.3843, 19.3908, 1.12584],
       "RRIP":   [10.5360, 18.3329, 1.19624],
       "I-RRIP": [9.92488, 13.9760, 1.02580]}
l2d = {"LRU":    [7.34592, 8.53252, 2.83320],
       "RRIP":   [7.07956, 7.96284, 2.84700],
       "I-RRIP": [7.71916, 9.18504, 2.88172]}
speedup = {p: [ipc[p][i] / ipc["LRU"][i] for i in range(3)] for p in policies}

def grouped(data, ylabel, title, name, decimals=2, ylim=None, hline=None):
    x, w = np.arange(len(traces)), 0.26
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    for i, p in enumerate(policies):
        bars = ax.bar(x + (i - 1) * w, data[p], w, label=p,
                      color=colors[p], edgecolor="black", linewidth=0.5)
        for b, v in zip(bars, data[p]):
            ax.annotate(f"{v:.{decimals}f}", (b.get_x() + b.get_width() / 2, v),
                        xytext=(0, 2), textcoords="offset points",
                        ha="center", va="bottom", fontsize=6.5)
    if hline is not None:
        ax.axhline(hline, color="red", ls="--", lw=1)
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xticks(x)
    ax.set_xticklabels(traces)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{OUT}/{name}.pdf")
    fig.savefig(f"{OUT}/{name}.png", dpi=200)
    plt.close(fig)
    print("wrote", name)

grouped(speedup, "Speedup over LRU", "Speedup (axis truncated)", "plot_speedup",
        decimals=4, ylim=(0.995, 1.025), hline=1.0)
grouped(ipc, "IPC", "IPC", "plot_ipc", decimals=4)
grouped(l2c, "MPKI", "L2C load MPKI", "plot_l2c_mpki", decimals=2)
grouped(l2i, "MPKI", "L2 instruction load MPKI", "plot_l2_instr_mpki", decimals=2)
grouped(l2d, "MPKI", "L2 data load MPKI", "plot_l2_data_mpki", decimals=2)