#!/usr/bin/env python3

import re, sys, math

R = "results_ckpt2"
SETUPS = ["baseline", "spp_fixed", "spp", "spp_bandpass"]


def read(p):
    try:
        with open(p, errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def lines_of(p):
    return [l.split() for l in read(p).replace("\r", "").splitlines() if l.strip()]


labels = [l[0] for l in lines_of("traces.txt")]
mixes = lines_of("mixes2.txt")
NM = len(mixes)


def roi_ipc(text):
    i = text.rfind("Region of Interest Statistics")
    seg = text[i:] if i >= 0 else text
    d = {}
    for m in re.finditer(r"CPU (\d+) cumulative IPC: ([\d.]+)", seg):
        d.setdefault(int(m.group(1)), float(m.group(2)))
    return [d[k] for k in sorted(d)]


if "--probe" in sys.argv:
    t = read(f"{R}/mix12_spp_bandpass.txt")
    for key in ["LLC Eviction Statistics", "Per-Core DRAM Statistics"]:
        i = t.rfind(key)
        print("=====", key, "found" if i >= 0 else "MISSING")
        if i >= 0:
            print("\n".join(t[i:].splitlines()[:25]))
    print("ROI IPC:", roi_ipc(t))
    sys.exit()

# ---------------------------------------------------------------- load
alone = {s: {} for s in SETUPS}
for s in SETUPS:
    for lb in labels:
        v = roi_ipc(read(f"{R}/alone_{s}_{lb}.txt"))
        if v:
            alone[s][lb] = v[0]

M = {s: {} for s in SETUPS}
bad = []
for s in SETUPS:
    for k in range(1, NM + 1):
        t = read(f"{R}/mix{k}_{s}.txt")
        ipc = roi_ipc(t)
        if len(ipc) != 4:
            bad.append(f"mix{k}_{s}")
        M[s][k] = (ipc, t)
if bad:
    print("WARNING: could not read 4 IPCs from:", bad)
    sys.exit(1)
for s in SETUPS:
    miss = [lb for lb in labels if lb not in alone[s]]
    if miss:
        print("WARNING: missing alone IPC for", s, miss)
        sys.exit(1)


def gmean(x):
    return math.exp(sum(math.log(v) for v in x) / len(x))


def mean(x):
    return sum(x) / len(x)


def mets(shared, ref):
    sd = [a / s for a, s in zip(ref, shared)]
    return dict(sd=sd, maxsd=max(sd), unf=max(sd) / min(sd),
                ws=sum(1 / x for x in sd), hs=len(sd) / sum(sd))


def ref_for(refname, k, s):
    src = s if refname == "own" else "baseline"
    return [alone[src][lb] for lb in mixes[k - 1]]


allk = list(range(1, NM + 1))
hetero = [k for k in allk if len(set(mixes[k - 1])) > 1]

# ---------------------------------------------------------------- 1. summary tables
print("1) SUMMARY  (maxSD, unfairness = arithmetic mean over mixes; WS, HS = geometric mean)")
print("   ref=base : every setup measured against BASELINE alone IPC (fair common yardstick)")
print("   ref=own  : every setup measured against its OWN alone IPC (interference only)")
for refname in ("base", "own"):
    for name, ks in (("all 16", allk), ("hetero", hetero)):
        print(f"\n[{refname}] {name} mixes ({len(ks)})")
        print(f"{'setup':13s} {'maxSD':>7s} {'unfair':>7s} {'WS':>7s} {'HS':>7s}")
        for s in SETUPS:
            rows = [mets(M[s][k][0], ref_for(refname, k, s)) for k in ks]
            print(f"{s:13s} {mean([r['maxsd'] for r in rows]):7.3f} {mean([r['unf'] for r in rows]):7.3f} "
                  f"{gmean([r['ws'] for r in rows]):7.3f} {gmean([r['hs'] for r in rows]):7.3f}")

print("\n[base] per-mix bandpass vs spp_fixed (HS change, threshold 0.5%)")
win = lose = tie = 0
for k in allk:
    a = mets(M["spp_bandpass"][k][0], ref_for("base", k, "spp_bandpass"))["hs"]
    b = mets(M["spp_fixed"][k][0], ref_for("base", k, "spp_fixed"))["hs"]
    d = a / b - 1
    if d > 0.005: win += 1
    elif d < -0.005: lose += 1
    else: tie += 1
print(f"bandpass better in {win}, worse in {lose}, within +-0.5% in {tie} of {NM} mixes")

# csv
with open("results_summary.csv", "w") as f:
    f.write("setup,mix,mixname,maxsd_own,unf_own,ws_own,hs_own,maxsd_base,unf_base,ws_base,hs_base\n")
    for s in SETUPS:
        for k in allk:
            o = mets(M[s][k][0], ref_for("own", k, s))
            b = mets(M[s][k][0], ref_for("base", k, s))
            f.write(f"{s},{k},{'+'.join(mixes[k-1])},{o['maxsd']:.4f},{o['unf']:.4f},{o['ws']:.4f},{o['hs']:.4f},"
                    f"{b['maxsd']:.4f},{b['unf']:.4f},{b['ws']:.4f},{b['hs']:.4f}\n")


# ---------------------------------------------------------------- 2. signals vs harm
def per_cpu(text, key, num=r"(\d+)"):
    out = {}
    for line in text.splitlines():
        if "CPU" in line:
            m = re.search(r"CPU\s*(\d+)", line)
            n = re.search(r"\b" + key + r"\s*[=:]\s*" + num, line)
            if m and n:
                out[int(m.group(1))] = float(n.group(1))
    return [out[i] for i in sorted(out)] if len(out) == 4 else None


def counters(text):
    c = {}
    c["suff"] = per_cpu(text, "CROSS_CORE_SUFFERED")
    c["caus"] = per_cpu(text, "CROSS_CORE_CAUSED")
    c["dpf"] = per_cpu(text, "DRAM_PREF_FRACTION", r"([\d.eE+-]+)")
    parts = [per_cpu(text, k) for k in ("LOAD", "RFO", "PREFETCH", "TRANSLATION", "WRITES")]
    c["dram"] = [sum(v) for v in zip(*parts)] if all(parts) else None
    return c


def ranks(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for t in range(i, j + 1):
            r[o[t]] = (i + j) / 2 + 1
        i = j + 1
    return r


def pearson(x, y):
    mx, my = mean(x), mean(y)
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return float("nan") if sx == 0 or sy == 0 else sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def demean(v):
    m = mean(v)
    return [a - m for a in v]


print("\n\n2) DO THE SIGNALS MATCH THE REAL HARM?  (hetero mixes, values demeaned within each mix,")
print("   Spearman rho pooled over mix-cores; own-alone reference; others_SD = mean slowdown of the OTHER 3 cores)")
for s in ("baseline", "spp_fixed", "spp_bandpass"):
    X = {"suff": [], "caus": [], "dram": [], "dpf": [], "sd": [], "osd": []}
    ok = True
    for k in hetero:
        c = counters(M[s][k][1])
        if c["suff"] is None or c["caus"] is None or c["dram"] is None or c["dpf"] is None:
            ok = False
            break
        sd = mets(M[s][k][0], ref_for("own", k, s))["sd"]
        osd = [(sum(sd) - x) / 3 for x in sd]
        for key, v in (("suff", c["suff"]), ("caus", c["caus"]), ("dram", c["dram"]), ("dpf", c["dpf"]),
                       ("sd", sd), ("osd", osd)):
            X[key] += demean(v)
    if not ok:
        print(f"{s}: PARSE FAIL for eviction/DRAM counters -> run: python3 analysis3.py --probe  and paste it")
        continue
    print(f"{s:13s} n={len(X['sd'])}  rho(evictions suffered, own SD)={spearman(X['suff'], X['sd']):+.2f}  "
          f"rho(evictions caused, others SD)={spearman(X['caus'], X['osd']):+.2f}  "
          f"rho(DRAM reqs, others SD)={spearman(X['dram'], X['osd']):+.2f}  "
          f"rho(DRAM pref frac, others SD)={spearman(X['dpf'], X['osd']):+.2f}")
print("   (+1 = signal ranks cores exactly like the real harm, 0 = no relation, - = opposite)")

# ---------------------------------------------------------------- 3. band-pass audit
BPRE = re.compile(
    r"CPU (\d+) BP-SPP Final Stats: Degree=\d+ Demands=(\d+) Prefetches=(\d+) Prefetch_Fraction=(\S+) "
    r"Useful=(\d+) Accuracy=(\S+)\s*Band-Pass Filter Details:\s*Candidate=(\d+) Issued=(\d+) "
    r"HP_Dropped=(\d+) LP_Dropped=(\d+) Epochs_InBand=(\d+) Epochs_HP=(\d+) Epochs_LP=(\d+)")


def bp_stats(text):
    d = {}
    for m in BPRE.finditer(text):
        g = m.groups()
        d[int(g[0])] = dict(pf=float(g[3]), acc=float(g[5]), cand=int(g[6]), iss=int(g[7]),
                            hpd=int(g[8]), lpd=int(g[9]), inb=int(g[10]), hp=int(g[11]), lp=int(g[12]))
    return d if len(d) == 4 else None


print("\n\n3) BAND-PASS DECISION AUDIT  (ipc ratio = bandpass IPC / spp_fixed IPC for the same core in the same mix)")
rows = []
pfs, accs = [], []
for k in allk:
    st = bp_stats(M["spp_bandpass"][k][1])
    if st is None:
        print(f"mix{k}: could not parse BP-SPP stats")
        continue
    for i in range(4):
        s_ = st[i]
        tot = s_["inb"] + s_["hp"] + s_["lp"]
        if tot == 0:
            continue
        ratio = M["spp_bandpass"][k][0][i] / M["spp_fixed"][k][0][i]
        others = mean([M["spp_bandpass"][k][0][j] / M["spp_fixed"][k][0][j] for j in range(4) if j != i])
        hp, lp = s_["hp"] / tot, s_["lp"] / tot
        pfs.append(s_["pf"]); accs.append(s_["acc"])
        tag = ""
        if hp > 0.5:
            tag = "HP-active; " + ("SUSPECT (acc>=0.5 or lost IPC)" if (s_["acc"] >= 0.5 or ratio < 0.98) else "justified")
        elif lp > 0.05:
            tag = "LP-active; others' IPC " + ("up" if others > 1.01 else "flat/down")
        elif hp > 0.05:
            tag = "HP partly"
        rows.append((abs(ratio - 1), k, i, mixes[k - 1][i], s_["pf"], s_["acc"], hp, lp, ratio, others, tag))
inband = sum(1 for r in rows if r[6] <= 0.05 and r[7] <= 0.05)
print(f"{inband} of {len(rows)} mix-cores stay in the pass-band (>95% of epochs) -> Band-Pass == spp_fixed there")
flagged = sorted([r for r in rows if r[10]], reverse=True)[:20]
print(f"{'mix':>4s} {'cpu':>3s} {'trace':8s} {'PF':>6s} {'acc':>5s} {'HP%':>5s} {'LP%':>5s} {'self':>6s} {'others':>6s}  verdict")
for r in flagged:
    print(f"{r[1]:4d} {r[2]:3d} {r[3]:8s} {r[4]:6.3f} {r[5]:5.2f} {100*r[6]:5.0f} {100*r[7]:5.0f} {r[8]:6.3f} {r[9]:6.3f}  {r[10]}")
if len(pfs) > 3:
    print(f"\nPaper's observation, tested: Spearman(prefetch fraction, accuracy) over {len(pfs)} mix-cores = "
          f"{spearman(pfs, accs):+.2f}  (paper reports ~0.7 with its own setup)")
print("NOTE: PF and accuracy here come from the final-stats line. 'Useful' uses a 256-entry recent-prefetch buffer,")
print("so accuracy is a lower bound. Keep this caveat in the report.")


try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    for a, (key, title) in zip(ax, (("maxsd", "Max slowdown (lower better)"),
                                     ("unf", "Unfairness (1 = equal)"),
                                     ("hs", "Harmonic speedup (higher better)"))):
        vals = []
        for s in SETUPS:
            r = [mets(M[s][k][0], ref_for("base", k, s))[key] for k in hetero]
            vals.append(gmean(r))
        a.bar(range(4), vals)
        a.set_xticks(range(4)); a.set_xticklabels(SETUPS, rotation=20, fontsize=8)
        a.set_title(title + "\nhetero mixes, ref = baseline alone", fontsize=9)
    plt.tight_layout(); plt.savefig("fig_summary.png", dpi=150)
    print("\nwrote fig_summary.png")
except Exception as e:
    print("\n(plot skipped:", e, ")")
print("wrote results_summary.csv")