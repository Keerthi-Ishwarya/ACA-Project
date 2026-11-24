import os
from metrics import ipcs

D = "results_ckpt2"
SETUPS = ["baseline", "spp_fixed", "spp"]

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

print("For every mix: the slowdown of each core (lower is better) and its IPC in the shared run (higher is better).")
print("Cores are listed in the order of the traces in the mix.\n")
for i, mix in enumerate(mixes, 1):
    print(f"mix{i}: {' '.join(mix)}")
    for s in SETUPS:
        p = f"{D}/mix{i}_{s}.txt"
        if not done(p) or any(t not in alone[s] for t in mix):
            print(f"   {s:10s} not finished")
            continue
        sh = ipcs(p)
        sd = [round(alone[s][t] / x, 2) for t, x in zip(mix, sh)]
        print(f"   {s:10s} slowdown {sd}   shared IPC {[round(x, 3) for x in sh]}")
    print()