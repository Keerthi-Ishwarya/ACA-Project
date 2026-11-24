import os
from metrics import ipcs, llc_evictions, dram_stats

D = "results_ckpt2"
SETUPS = ["baseline", "spp_fixed", "spp", "spp_bandpass"]

def done(p):
    return os.path.exists(p) and "Region of Interest Statistics" in open(p).read()

labels = [l.split()[0] for l in open("traces.txt") if l.strip()]
mixes = [l.split() for l in open("mixes2.txt") if l.strip()]

alone = {s: {} for s in SETUPS}
for s in SETUPS:
    for lab in labels:
        p = f"{D}/alone_{s}_{lab}.txt"
        if done(p):
            alone[s][lab] = ipcs(p)[0]

print("For every mix: the slowdown of each core (lower is better), shared IPC, and interference counters.")
print("Cores are listed in the order of the traces in the mix.\n")
for i, mix in enumerate(mixes, 1):
    print(f"============================================================")
    print(f"Mix {i}: {' '.join(mix)}")
    print(f"============================================================")
    for s in SETUPS:
        p = f"{D}/mix{i}_{s}.txt"
        if not done(p) or any(t not in alone[s] for t in mix):
            print(f"   {s:14s} not finished")
            continue
        sh = ipcs(p)
        sd = [round(alone[s][t] / x, 2) for t, x in zip(mix, sh)]
        print(f"   {s:14s} slowdown: {sd}")
        print(f"   {'':14s} shared IPC: {[round(x, 3) for x in sh]}")

        # Check if interference counters are present
        ev = llc_evictions(p)
        ds = dram_stats(p)
        if ev["suffered"]:
            suff = [ev["suffered"].get(c, 0) for c in range(len(mix))]
            caused = [ev["caused"].get(c, 0) for c in range(len(mix))]
            print(f"   {'':14s} LLC cross evictions suffered: {suff}")
            print(f"   {'':14s} LLC cross evictions caused:   {caused}")
        if ds:
            dr_total = [ds[c]["total"] for c in range(len(mix)) if c in ds]
            dr_pf = [round(ds[c]["pf_fraction"], 3) for c in range(len(mix)) if c in ds]
            print(f"   {'':14s} DRAM requests total:          {dr_total}")
            print(f"   {'':14s} DRAM prefetch fraction:       {dr_pf}")
    print()
