from metrics import ipcs
mixes = [l.split() for l in open("mixes.txt") if l.strip()]
for setup in ["baseline", "spp", "spp_fixed"]:
    alone = {t: ipcs(f"results/alone_{setup}_{t}.txt")[0] for t in ["T1", "T2", "T3"]}
    print(setup, "alone IPC:", {t: round(v, 3) for t, v in alone.items()})
    for i, mix in enumerate(mixes, 1):
        sh = ipcs(f"results/mix{i}_{setup}.txt")
        sd = [round(alone[t] / s, 2) for t, s in zip(mix, sh)]
        flag = "   <-- slowdown below 1, check!" if min(sd) < 0.98 else ""
        print(f"  mix{i}", " ".join(mix), "slowdowns:", sd, flag)
