T1=/mnt/d/traces/Trace1-002.champsimtrace.gz; T2=/mnt/d/traces/Trace2-003.champsimtrace.gz; T3=/mnt/d/traces/Trace3-001.champsimtrace.gz
for s in baseline spp spp_fixed; do
  new=$(ls bin/*-4core-${s}_4c 2>/dev/null); old=$(ls /mnt/d/CS368_Project/bin/*-4core-${s}_4c 2>/dev/null)
  if [ -z "$new" ] || [ -z "$old" ]; then echo "MISSING BINARY for $s"; continue; fi
  a=$($new -warmup_instructions 1000000 -simulation_instructions 1000000 -traces $T1 $T2 $T3 $T1 | grep "^CPU . cumulative IPC" | tail -4)
  b=$($old -warmup_instructions 1000000 -simulation_instructions 1000000 -traces $T1 $T2 $T3 $T1 | grep "^CPU . cumulative IPC" | tail -4)
  [ "$a" = "$b" ] && echo "MATCH     $s" || echo "DIFFERENT $s"
done
