#!/bin/bash
# Gathers the code that the counter edits need into one text file (D:\for_claude.txt).
# Usage: bash collect.sh
OUTFILE=${OUTFILE:-/mnt/d/for_claude.txt}
[ -d /mnt/d/ACA_counters ] || git clone /mnt/d/ACA_project /mnt/d/ACA_counters
cd /mnt/d/ACA_counters || exit 1

show() {   # show <pattern> <file> <number of lines after the first match>
  n=$(grep -n "$1" "$2" | head -1 | cut -d: -f1)
  if [ -n "$n" ]; then sed -n "${n},$((n+$3))p" "$2"; else echo "NOT FOUND: $1 in $2"; fi
}

{
echo "##### cache.cc fill_cache (lines 2855-2990)";           sed -n '2855,2990p' src/cache.cc
echo "##### cache.cc prefetch_line area (lines 3590-3730)";   sed -n '3590,3730p' src/cache.cc
echo "##### dram_controller.cc add_rq";  show "MEMORY_CONTROLLER::add_rq" src/dram_controller.cc 70
echo "##### dram_controller.cc add_wq";  show "MEMORY_CONTROLLER::add_wq" src/dram_controller.cc 60
echo "##### dram_controller.h";          sed -n '1,90p' inc/dram_controller.h
echo "##### cache.h";                    sed -n '1,215p' inc/cache.h
echo "##### block.h";                    cat inc/block.h
echo "##### main.cc functions"
show "^void reset_cache_stats"  src/main.cc 40
show "^void record_roi_stats"   src/main.cc 40
show "^void print_roi_stats"    src/main.cc 120
show "print_dram_stats"         src/main.cc 40
show "reset_dram_stats"         src/main.cc 20
echo "##### main.cc call sites"
for n in $(grep -n "record_roi_stats(\|reset_cache_stats(\|print_roi_stats(\|print_dram_stats(" src/main.cc | cut -d: -f1); do
  a=$((n>6 ? n-6 : 1))
  echo "--- main.cc around line $n"; sed -n "${a},$((n+6))p" src/main.cc
done
} > "$OUTFILE"
wc -l "$OUTFILE"
grep -c "NOT FOUND" "$OUTFILE" | sed 's/^/sections not found: /'
