# Do fair prefetching methods really work on a shared cache?

## What this is

When so many LLC and memory, the prefetcher of one core can push out another core's data and use up memory bandwidth. Some papers try to fix this by controlling how much each core prefetches. This project checks, in ChampSim with 4 cores, whether one such method (Band-Pass prefetching, Sridharan et al., TACO 2017) really makes slowdowns more equal.

I changed ChampSim to measure the interference directly, wrote a simplified Band-Pass controller, and compared four setups on 16 four-core mixes.

## The four setups

| name | what it does |
|---|---|
| `baseline` | no prefetcher |
| `spp_fixed` | SPP-style prefetcher at L1D, always up to 4 lines ahead, no control |
| `spp` | same prefetcher with my PA2 accuracy throttling |
| `spp_bandpass` | same prefetcher plus the Band-Pass drop filter |

## What I added to ChampSim

- **Cross-core LLC evictions.** When a fill pushes out a valid block, I check whether the old block belonged to another core. Per-core "caused" and "suffered" counts and a 4x4 table (who evicted whom) are printed. Code: `inc/cache.h`, `src/cache.cc`, `src/main.cc`.
- **Per-core DRAM requests.** Loads, RFOs, prefetches, translations and writes are counted for each core, and the DRAM prefetch fraction is printed. Code: `inc/dram_controller.h`, `src/dram_controller.cc`, `src/main.cc`.
- **Prefetch fraction at L1D.** `prefetcher/spp.l1d_pref` and `prefetcher/spp_fixed.l1d_pref` print demands, prefetches and the fraction.
- **Band-Pass controller.** `prefetcher/spp_bandpass.l1d_pref`.

All counters are reset when warm-up ends, so they only cover the measured part.

## How my Band-Pass works

Each core counts the prefetches its prefetcher wants to send (candidates, counted before
any are dropped) and its L1D accesses. Every 16,384 (2^14) L1D accesses it computes (i took that number because I first tried 1,024 accesses, but then mcf kept jumping between zones from one epoch to
the next, which looked like noise. The paper uses 1 million LLC misses, but it runs 300M
instructions per program on 16 cores. My runs are 10M instructions per core, so an epoch
that long would give very few epochs. I picked 16,384, between the two. I did not test
other values) 

    PF = candidates / (L1D accesses + candidates)

and picks a zone for the next epoch:

- PF below 0.21: issue 1 prefetch in 16, drop the rest
- PF between 0.21 and 0.50: issue everything
- PF above 0.50: issue 1 in 2

The thresholds and drop rates come from the paper. The epoch length is my own choice and I did not sweep it.

### Differences from the paper

- The paper's low-pass part is global: it checks whether demands wait longer than prefetches in memory and whether prefetches outnumber demands in the whole system, then slows only the one worst core. Mine is local: each core only looks at its own PF.
- The paper controls an L2 stream prefetcher. I control an SPP-style prefetcher at L1D.
- The paper uses epochs of 1 million LLC misses, 16 cores, 300M instructions. I use 16,384 demand misses, 4 cores, 10M instructions.
- Thresholds were not re-tuned for this simulator.

The FST-style controller from my proposal is **not done** (not enough time).

## Files

| file | purpose |
|---|---|
| `traces.txt` | trace label and path (paths are for my machine; trace files are not in the repo) |
| `mixes2.txt` | the 16 mixes, four trace labels per line |
| `run2.sh` | runs all simulations |
| `results_ckpt2/` | raw simulator output for all 100 runs |
| `results_ckpt2_bp_v1/` | first Band-Pass runs, before I fixed a bug in the look-ahead code. Kept only for comparison. |


## How to reproduce

1. Build the eight binaries (1-core and 4-core for each of the four setups):
   
       bash build_all.sh

   This calls `./build_champsim.sh <L1D prefetcher> lru <name> <cores>` 8, for
   `no` (baseline), `spp_fixed`, `spp` and `spp_bandpass`, each with 1 and 4 cores.
   

3. Run the simulations (10M warm-up + 10M measured instructions, 6 jobs at a time):

       bash run2.sh 6 baseline spp_fixed spp spp_bandpass

   `run2.sh` skips runs whose output already contains `Per-Core DRAM Statistics`. To rerun one setup, delete its files in `results_ckpt2/` first. `FORCE=1` reruns everything, so be careful with it.

4. Check that every run finished:

       for f in results_ckpt2/*.txt; do
         grep -q "Region of Interest Statistics" "$f" || echo "not done: $f"
       done


## Limits

- Only Band-Pass-style control was tested. FST and HPAC were not.
- 9 traces, 16 mixes, one run per setup and mix, 10M instructions.
- Accuracy is a lower bound, because "useful" is checked against a 256-entry list of recent prefetches.
- The correlations use only 12 mixed mixes.

