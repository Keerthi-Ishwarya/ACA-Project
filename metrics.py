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
