#!/bin/bash
P=${1:-2}
rm -f jobs_fixed.txt
T1=/mnt/d/traces/Trace1-002.champsimtrace.gz
T2=/mnt/d/traces/Trace2-003.champsimtrace.gz
T3=/mnt/d/traces/Trace3-001.champsimtrace.gz
W=25000000; S=25000000
setup=spp_fixed
B1=$(ls bin/*-1core-${setup}_1c); B4=$(ls bin/*-4core-${setup}_4c)
for t in T1 T2 T3; do
  echo "$B1 -warmup_instructions $W -simulation_instructions $S -traces ${!t} > results/alone_${setup}_$t.txt" >> jobs_fixed.txt
done
m=0
while read -r a b c d; do
  m=$((m+1))
  echo "$B4 -warmup_instructions $W -simulation_instructions $S -traces ${!a} ${!b} ${!c} ${!d} > results/mix${m}_${setup}.txt" >> jobs_fixed.txt
done < mixes.txt
wc -l jobs_fixed.txt
xargs -P $P -I{} sh -c "{}" < jobs_fixed.txt
