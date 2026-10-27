# Do Fair Prefetching Methods Really Work on a Shared Cache?

**Status: checkpoint 1 complete.** repo contains working 4core ChampSim setup, scripts that run the experiments and compute fairness metrics,  results of 33 simulations. Checkpoint 2 (direct interference counters and fairness-oriented controllers) in progress.

## The question

Cores of multi-core processor share the LLC and the DRAM bandwidth, so the prefetcher of one core can slow down the other cores. FST, P-FST, HPAC and Band-Pass Prefetching control prefetchers to reduce this interference, but each paper tests its own method in its own simulator. This project re tests such methods in ChampSim and asks:

1. Do they make the slowdowns of the cores more equal?
2. Do the signals they use match the real harm?
3. What do they cost in speed?

Checkpoint 1 measures how unfair the shared system is **without** any fairness control. This is the baseline for the methods of checkpoint 2.

## Main results of checkpoint 1

Eight four core mixes of 3 traces (T1, T2, T3), three setups, 25M warmup + 25M simulated instructions per core. GM over the 5 mixed workloads (mixes 4 to 8). Slowdown = IPC alone divided by IPC shared, and unfairness = largest slowdown / the smallest (1 means equal).

| Setup | Max. slowdown (lower is better) | Unfairness (lower is better) | Weighted speedup (higher is better) | Harmonic speedup (higher is better) |
|---|---|---|---|---|
| No prefetcher | 1.408 | 1.242 | 3.172 | 0.785 |
| Fixed degree 4 ("no control") | 1.442 | 1.265 | 3.134 | 0.774 |
| Throttled degree 1-4 (PA2 accuracy throttling) | 1.436 | 1.263 | 3.141 | 0.776 |

- The mixed workloads are unfair (unfairness up to 1.39), and the PA2 accuracy throttling changes the unfairness by at most 0.008 compared with a fixed degree.
- Most of the unfairness comes from the different sensitivity of the traces to sharing (T1 slows down by 1.40 to 1.62, T3 by 1.10 to 1.16 whatever its neighbours are), not from visible harm of one core to another. Checkpoint 2 tests this with direct counters.
- All per-mix numbers are in `results_table_ckpt1.csv`

## Environment

- Ubuntu under WSL2 on Windows, GCC 13, Python 3 
- A 4-core run needs roughly 100 to 200 MB of RAM.
- The simulator is deterministic: same run gives same IPC.
- **Traces are not included.** The three traces are the ones provided for PA2 (`Trace1-002`, `Trace2-003`, `Trace3-001`, `.champsimtrace.gz`). The scripts expect them in `/mnt/d/traces/`; change the variables `T1`, `T2`, `T3` at the top of `run_all.sh` and `run_fixed.sh` if they are elsewhere.

## Repository layout

| Path | Content |
|---|---|
| `src/`, `inc/`, `branch/`, `replacement/` | ChampSim sources (PA2 base, with the changes listed below) |
| `prefetcher/spp.l1d_pref` | Throttled prefetcher (PA2 accuracy throttling), per-core state |
| `prefetcher/spp_fixed.l1d_pref` | Same prefetcher with the degree fixed to 4 (the "no control" setup) |
| `prefetcher/ip_stride.l1d_pref`, `prefetcher/no.l1d_pref` | Stride prefetcher and "no prefetcher" from the base |
| `build_champsim.sh` | Build script with an optional number of cores |
| `mixes.txt` | The eight four-core mixes, one per line |
| `run_all.sh` | Runs the alone runs and the eight mixes for the `baseline` and `spp` setups (22 jobs) |
| `run_fixed.sh` | The same for the `spp_fixed` setup (11 jobs) |
| `metrics.py`, `report.py`, `percore.py` | Metrics library, table of metrics per mix, slowdown of every core |
| `reap.sh` | Optional watcher that stops finished simulations that linger and block the job queue |
| `results/` | Raw ChampSim output of all 33 runs |
| `results_table_ckpt1.csv` | Metrics of all mixes and setups |
| `scripts/` | Helper scripts inherited from the PA2 base (not used by the project scripts) |

Naming in the results: `baseline` means no prefetcher, `spp` means the throttled prefetcher, `spp_fixed` means the fixed-degree prefetcher. Files are `results/alone_<setup>_<trace>.txt` and `results/mix<k>_<setup>.txt`.

## Simulated system

4 cores with a hashed perceptron branch predictor, a shared 8 MB 16-way LLC (8192 sets) with LRU, one DRAM channel shared by all cores, LRU at all cache levels, L1D prefetcher as selected by the setup. The LLC size is fixed to the four-core value in `inc/cache.h` for **every** build, so that the alone runs (one core) and the shared runs (four cores) use the same cache.

## Build

```bash
# 1 = number of cores. Usage: ./build_champsim.sh <L1D prefetcher> <replacement> <binary name> [num_core]
./build_champsim.sh no        lru baseline_1c   1
./build_champsim.sh spp       lru spp_1c        1
./build_champsim.sh spp_fixed lru spp_fixed_1c  1
./build_champsim.sh no        lru baseline_4c   4
./build_champsim.sh spp       lru spp_4c        4
./build_champsim.sh spp_fixed lru spp_fixed_4c  4
ls bin
```

**Important:** the build script temporarily changes `NUM_CPUS` in `inc/champsim.h` and restores it afterwards. If a build fails, the file can stay at the wrong value. Before every build, check that this prints `1`, and run builds one after another, never in parallel:

```bash
grep -n "define NUM_CPUS" inc/champsim.h
```

## Sanity check (about 1 minute)

One core, `Trace1-002`, 1M warm-up and 1M simulated instructions:

```bash
T1=/path/to/Trace1-002.champsimtrace.gz
./bin/*-1core-spp_1c       -warmup_instructions 1000000 -simulation_instructions 1000000 -traces $T1 | grep "^CPU 0 cumulative IPC"
./bin/*-1core-spp_fixed_1c -warmup_instructions 1000000 -simulation_instructions 1000000 -traces $T1 | grep -E "^CPU 0 cumulative IPC|Degree"
```

Expected: IPC `0.234648` for `spp`, and IPC `0.235071` with `Degree=4` for `spp_fixed`.

## Run the experiments

```bash
bash run_all.sh 4      # alone runs and mixes for baseline and spp, 4 jobs in parallel
bash run_fixed.sh 2    # alone runs and mixes for spp_fixed, 2 jobs in parallel
```

Each one-core run takes about 2-3 minutes and each four-core run about 25 minutes. All 33 runs take about two hours with 6 parallel jobs on a laptop with 8 threads. A run is finished when its output file contains `Region of Interest Statistics`:

```bash
for f in results/alone_*.txt results/mix*.txt; do
  grep -q "Region of Interest Statistics" "$f" || echo "not done: $f"
done
```

If finished simulations stay alive after printing their statistics and block the job queue, run `nohup bash reap.sh > reap.log 2>&1 &` while the batch runs, and stop it with `pkill -f reap.sh` afterwards.

## Compute the metrics

```bash
python3 report.py      # prints the metrics of every mix and setup, writes results_table.csv
python3 percore.py     # prints the slowdown of every core, plus the alone IPC of each trace
```

Definitions (N = 4 cores): speedup = IPC shared / IPC alone, slowdown = 1 / speedup, maximum slowdown = largest slowdown, unfairness = largest slowdown / smallest slowdown, weighted speedup = sum of speedups, harmonic speedup = N / sum of (1 / speedup). Ratios are summarized across mixes with the geometric mean.

## Changes to the base code

1. `src/page_table_walker.cc`, `inc/page_table_walker.h`: `handle_page_fault` declares a return value but returns nothing, which crashes multi-core runs under GCC 13; it returns `void`.
2. `src/main.cc`: `index` is initialized, and the context-switch index is guarded when the option is absent.
3. `build_champsim.sh`: optional fourth argument for the number of cores.
4. `inc/cache.h` (lines 102 to 107): the LLC sets and queue sizes use the four-core values for every build.
5. `prefetcher/spp.l1d_pref`: all tables and counters are per core (`[NUM_CPUS]`), and the confidence cap now applies to the tracker in use (the base code capped the first tracker only).
6. `prefetcher/spp_fixed.l1d_pref` (new): the same prefetcher with the degree fixed to 4.

## Plan for checkpoint 2

- Add counters for cross-core evictions, per-core DRAM requests and the prefetch fraction, and test them on a tiny example.
- Implement simplified FST-style and Band-Pass controllers (HPAC-style control if time allows) and compare them with no control and the PA2 throttling on more mixes.
- Add more traces, especially traces on which prefetching matters.
- Analyse whether the slowdowns become more equal, whether the signals match the real harm, what the speed cost is, and where the controllers decide wrongly.

## Limitations

Three traces and eight mixes (three of them same-trace control mixes), one DRAM channel, and a prefetcher that changes the IPC of these traces by at most 0.009. The slowdowns of different setups are relative to different alone runs and are not directly comparable.

## Credits

- ChampSim: https://github.com/ChampSim/ChampSim (see `LICENSE`).
- The base code is the version of ChampSim used for the CS683 assignment PA2, including the accuracy-throttled prefetcher. <!-- If PA2 was done with a teammate, name them here. -->
- Papers: FST (Ebrahimi et al., ASPLOS 2010), P-FST (Ebrahimi et al., ISCA 2011), HPAC (Ebrahimi et al., MICRO 2009), Band-Pass Prefetching (Sridharan, Panda, Seznec, TACO 2017).
