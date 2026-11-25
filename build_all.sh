#!/bin/bash
for cfg in "no baseline_1c 1" "spp_fixed spp_fixed_1c 1" "spp spp_1c 1" "spp_bandpass spp_bandpass_1c 1" \
mkdir -p bin obj/src obj/branch obj/prefetcher obj/replacement
           "no baseline_4c 4" "spp_fixed spp_fixed_4c 4" "spp spp_4c 4" "spp_bandpass spp_bandpass_4c 4"; do
  set -- $cfg
  grep -q "define NUM_CPUS 1" inc/champsim.h || { echo "NUM_CPUS is not 1, stop"; break; }
  ./build_champsim.sh $1 lru $2 $3 2>&1 | tail -2
done
