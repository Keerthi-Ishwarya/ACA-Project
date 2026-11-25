#!/bin/bash
# Usage: bash run2.sh [parallel_jobs] [setups...]     eg..  bash run2.sh 4 baseline spp_fixed spp spp_bandpass

P=${1:-4}; shift
SETUPS=${*:-baseline spp_fixed spp spp_bandpass}
W=${W:-10000000}; S=${S:-10000000}
mkdir -p results_ckpt2
declare -A TP
while read -r label path; do
  [ -n "$label" ] && TP[$label]=$path
done < <(tr -d '\r' < traces.txt)
rm -f jobs2.txt
for setup in $SETUPS; do
  B1=$(ls bin/*-1core-${setup}_1c 2>/dev/null | head -1); B4=$(ls bin/*-4core-${setup}_4c 2>/dev/null | head -1)
  if [ -z "$B1" ] || [ -z "$B4" ]; then echo "missing binary for $setup"; exit 1; fi
  for label in "${!TP[@]}"; do
    out=results_ckpt2/alone_${setup}_${label}.txt
    if [ "$FORCE" = "1" ] || ! grep -q "Per-Core DRAM Statistics" $out 2>/dev/null; then
      echo "$B1 -warmup_instructions $W -simulation_instructions $S -traces ${TP[$label]} > $out" >> jobs2.txt
    fi
  done
  m=0
  while read -r a b c d; do
    [ -z "$a" ] && continue
    m=$((m+1))
    out=results_ckpt2/mix${m}_${setup}.txt
    if [ "$FORCE" = "1" ] || ! grep -q "Per-Core DRAM Statistics" $out 2>/dev/null; then
      echo "$B4 -warmup_instructions $W -simulation_instructions $S -traces ${TP[$a]} ${TP[$b]} ${TP[$c]} ${TP[$d]} > $out" >> jobs2.txt
    fi
  done < <(tr -d '\r' < mixes2.txt)
done
[ -f jobs2.txt ] || { echo "nothing to run"; exit 0; }
wc -l jobs2.txt
xargs -P $P -I{} sh -c "{} || true" < jobs2.txt
