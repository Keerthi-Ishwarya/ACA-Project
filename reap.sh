#!/bin/bash
while true; do
  for pid in $(pgrep -f "^bin/hashed_perceptron"); do
    f=$(readlink /proc/$pid/fd/1) || continue
    [ -f "$f" ] || continue
    if grep -q "Allocated PAGES" "$f" && [ $(( $(date +%s) - $(stat -c %Y "$f") )) -gt 60 ]; then
      echo "$(date +%T) reaping $pid ($f)"; kill -TERM $pid
    fi
  done
  sleep 30
done
