#!/bin/bash
BENCHMARKS=("3d7pt" "apop" "game-of-life" "heat-1d" "heat-2d" "heat-3d")

TIMESTAMP=$(date +"%Y-%m-%d-%H-%M")
OUTPUT_DIR="/home/marteau/test_flav/results/res_${TIMESTAMP}"
PLUTO_BENCH_DIR="/home/marteau/pesto-bench/pluto_bench"
INC_DIR="/home/marteau/pesto-bench/include"
LIB_DIR="/home/marteau/pesto-bench/lib"

mkdir -p "$OUTPUT_DIR"

for BENCH in "${BENCHMARKS[@]}"; do
    SRC_FILE=$(ls "$PLUTO_BENCH_DIR/$BENCH"/*.c 2>/dev/null | head -n 1)
    EXE="$PLUTO_BENCH_DIR/$BENCH/$BENCH"

    [ ! -f "$SRC_FILE" ] && echo "[SKIP] $BENCH" && continue

    echo -n "[COMPILE] $BENCH... "
    gcc -O3 -march=native -fopenmp -I "$INC_DIR" "$SRC_FILE" -o "$EXE" -L "$LIB_DIR" -lbenchmark -lm -fopenmp || { echo "ÉCHEC"; continue; }
    echo "OK"

    echo -n "[RUN] $BENCH... "
    RESULT=$("$EXE" | grep -E "^[0-9.]+$" | tail -n 1)
    [ -z "$RESULT" ] && RESULT=$({ /usr/bin/time -f "%e" "$EXE" > /dev/null; } 2>&1)
    echo "$RESULT" | tee "$OUTPUT_DIR/${BENCH}.txt"

    # rm -f "$EXE"
done

echo "Terminé. Résultats dans $OUTPUT_DIR"