#!/bin/bash
# ==============================================================================
# CONFIGURATION ÉDITABLE
# ==============================================================================
BENCHMARKS=("3d7pt" "apop" "game-of-life" "heat-1d" "heat-2d" "heat-3d")

NUM_RUNS=20              # Nombre de répétitions (N)
MAX_PARALLEL=60          # Nombre max de jobs en parallèle

TIMESTAMP=$(date +"%Y-%m-%d-%H-%M")
BASE_OUTPUT_DIR="test_flav/results/res"
OUTPUT_DIR="${BASE_OUTPUT_DIR}_${TIMESTAMP}"

PLUTO_BENCH_DIR="/home/marteau/pesto-bench/pluto_bench"
INC_DIR="/home/marteau/pesto-bench/include"
LIB_DIR="/home/marteau/pesto-bench/lib"
LIB_NAME="benchmark"

CC="gcc"
CFLAGS="-O3 -I $INC_DIR"
LDFLAGS="-L $LIB_DIR -l$LIB_NAME -lm"

# ==============================================================================
# PRÉPARATION
# ==============================================================================
mkdir -p "$OUTPUT_DIR"
echo "--- Début de la campagne de tests ---"
echo "Nombre de runs par test : $NUM_RUNS"
echo "Parallélisme max       : $MAX_PARALLEL"
echo "-------------------------------------"

# ==============================================================================
# FONCTIONS
# ==============================================================================

# Lance un seul run et écrit le résultat dans un fichier temporaire
run_single() {
    local EXE="$1"
    local TMP_FILE="$2"

    TIME_RESULT=$("$EXE" | grep -E "^[0-9.]+$" | tail -n 1)
    if [ -z "$TIME_RESULT" ]; then
        TIME_RESULT=$({ /usr/bin/time -f "%e" "$EXE" > /dev/null; } 2>&1)
    fi
    echo "$TIME_RESULT" > "$TMP_FILE"
}

# Attend qu'il y ait moins de MAX_PARALLEL jobs en arrière-plan
wait_for_slot() {
    while [ "$(jobs -rp | wc -l)" -ge "$MAX_PARALLEL" ]; do
        sleep 0.05
    done
}

# ==============================================================================
# BOUCLE PRINCIPALE
# ==============================================================================
for BENCH in "${BENCHMARKS[@]}"; do
    SRC_DIR="$PLUTO_BENCH_DIR/$BENCH"
    SRC_FILE=$(ls $SRC_DIR/*.c 2>/dev/null | head -n 1)
    EXE="$SRC_DIR/${BENCH}_$$"          # suffixe PID pour éviter les conflits
    CSV_FILE="$OUTPUT_DIR/${BENCH}_results.csv"
    TMP_DIR="$OUTPUT_DIR/.tmp_${BENCH}"

    if [ ! -f "$SRC_FILE" ]; then
        echo "[SKIP] Source non trouvée pour $BENCH"
        continue
    fi

    # 1. COMPILATION
    echo -n "[1/2] Compilation de $BENCH... "
    $CC $CFLAGS "$SRC_FILE" -o "$EXE" $LDFLAGS
    if [ $? -ne 0 ]; then
        echo "ÉCHEC"
        continue
    fi
    echo "OK"

    # 2. EXÉCUTION PARALLÈLE
    echo "[2/2] Exécution de $BENCH ($NUM_RUNS runs, max $MAX_PARALLEL en parallèle)..."
    mkdir -p "$TMP_DIR"

    for (( i=1; i<=NUM_RUNS; i++ )); do
        wait_for_slot
        run_single "$EXE" "$TMP_DIR/run_${i}.txt" &
    done

    # Attendre que tous les runs de ce benchmark soient finis
    wait

    # 3. AGRÉGATION DES RÉSULTATS dans le CSV
    echo "run_id,execution_time" > "$CSV_FILE"
    for (( i=1; i<=NUM_RUNS; i++ )); do
        TIME_RESULT=$(cat "$TMP_DIR/run_${i}.txt" 2>/dev/null)
        echo "$i,$TIME_RESULT" >> "$CSV_FILE"
    done
    rm -rf "$TMP_DIR"

    echo "Terminé. Résultats dans $CSV_FILE"
    echo "-------------------------------------"
    echo "Ménage $EXE"
    rm -f "$EXE"
done

echo "Tests terminés avec succès."