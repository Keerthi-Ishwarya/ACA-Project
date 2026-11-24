import re

def ipcs(path):
    d = {}
    for m in re.finditer(r"CPU (\d+) cumulative IPC: ([\d.]+)", open(path).read()):
        d[int(m.group(1))] = float(m.group(2))   
    return [d[i] for i in sorted(d)]

def metrics(shared, alone):
    sp = [s / a for s, a in zip(shared, alone)]   
    return {
        "max_slowdown": max(1 / x for x in sp),
        "unfairness": max(sp) / min(sp),          
        "weighted_speedup": sum(sp),
        "harmonic_speedup": len(sp) / sum(1 / x for x in sp),
    }

def llc_evictions(path):
    text = open(path).read()
    caused = {}
    suffered = {}
    same = {}
    total = {}
    for m in re.finditer(r"CPU (\d+) LLC Evictions:\s*TOTAL:\s*(\d+)\s*SAME_CORE:\s*(\d+)\s*CROSS_CORE_CAUSED:\s*(\d+)\s*CROSS_CORE_SUFFERED:\s*(\d+)", text):
        c = int(m.group(1))
        total[c] = int(m.group(2))
        same[c] = int(m.group(3))
        caused[c] = int(m.group(4))
        suffered[c] = int(m.group(5))
    return {"total": total, "same": same, "caused": caused, "suffered": suffered}

def dram_stats(path):
    text = open(path).read()
    dram = {}
    for m in re.finditer(r"CPU (\d+) DRAM Requests:\s*TOTAL:\s*(\d+)\s*READS:\s*(\d+)\s*\(LOAD:\s*(\d+),\s*RFO:\s*(\d+),\s*PREFETCH:\s*(\d+),\s*TRANSLATION:\s*(\d+)\)\s*WRITES:\s*(\d+)\s*DRAM_PREF_FRACTION:\s*([\d.]+)", text):
        c = int(m.group(1))
        dram[c] = {
            "total": int(m.group(2)),
            "reads": int(m.group(3)),
            "load": int(m.group(4)),
            "rfo": int(m.group(5)),
            "prefetch": int(m.group(6)),
            "translation": int(m.group(7)),
            "writes": int(m.group(8)),
            "pf_fraction": float(m.group(9))
        }
    return dram

def l1d_pf_stats(path):
    text = open(path).read()
    stats = {}
    for m in re.finditer(r"CPU (\d+) (?:SPP|BP-SPP) Final Stats:.*?Demands=(\d+)\s+Prefetches=(\d+)\s+Prefetch_Fraction=([\d.]+)", text):
        c = int(m.group(1))
        stats[c] = {
            "demands": int(m.group(2)),
            "prefetches": int(m.group(3)),
            "pf_fraction": float(m.group(4))
        }
    return stats
