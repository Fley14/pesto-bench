#!/bin/bash
# ==============================================================================
# CONFIGURATION ÉDITABLE
# ==============================================================================
BENCHMARKS=("3d7pt" "apop" "game-of-life" "heat-1d" "heat-2d" "heat-3d")

NUM_RUNS=20
MAX_PARALLEL=60

TIMESTAMP=$(date +"%Y-%m-%d-%H-%M")
BASE_OUTPUT_DIR="/home/marteau/test_flav/results/res"
OUTPUT_DIR="${BASE_OUTPUT_DIR}_${TIMESTAMP}"

PLUTO_BENCH_DIR="/home/marteau/pesto-bench/pluto_bench"
INC_DIR="/home/marteau/pesto-bench/include"
LIB_DIR="/home/marteau/pesto-bench/lib"
LIB_NAME="benchmark"

CC="gcc"
CFLAGS="-O3 -I $INC_DIR -march=native -fopenmp"
LDFLAGS="-L $LIB_DIR -l$LIB_NAME -lm"

# ==============================================================================
# PRÉPARATION
# ==============================================================================
mkdir -p "$OUTPUT_DIR"
TMP_DIR="$OUTPUT_DIR/.tmp"
mkdir -p "$TMP_DIR"

echo "--- Début de la campagne de tests ---"
echo "Nombre de runs par test : $NUM_RUNS"
echo "Parallélisme max       : $MAX_PARALLEL"
echo "-------------------------------------"

# ==============================================================================
# PHASE 1 : COMPILATION DE TOUS LES BENCHMARKS
# ==============================================================================
declare -A EXE_MAP   # bench -> chemin exécutable

for BENCH in "${BENCHMARKS[@]}"; do
    SRC_DIR="$PLUTO_BENCH_DIR/$BENCH"
    SRC_FILE=$(ls "$SRC_DIR"/*.c 2>/dev/null | head -n 1)
    EXE="$TMP_DIR/${BENCH}_exe"

    if [ ! -f "$SRC_FILE" ]; then
        echo "[SKIP] Source non trouvée pour $BENCH"
        continue
    fi

    echo -n "[COMPILE] $BENCH... "
    $CC $CFLAGS "$SRC_FILE" -o "$EXE" $LDFLAGS
    if [ $? -ne 0 ]; then
        echo "ÉCHEC"
        continue
    fi
    echo "OK"
    EXE_MAP["$BENCH"]="$EXE"
done

echo "-------------------------------------"
echo "Compilation terminée. Lancement du pool de workers..."
echo "-------------------------------------"

# ==============================================================================
# PHASE 2 : POOL GLOBAL — file de toutes les exécutions à faire
# ==============================================================================

# Fonction exécutée par chaque worker
run_job() {
    local EXE="$1"
    local OUT_FILE="$2"

    TIME_RESULT=$("$EXE" | grep -E "^[0-9.]+$" | tail -n 1)
    if [ -z "$TIME_RESULT" ]; then
        TIME_RESULT=$({ /usr/bin/time -f "%e" "$EXE" > /dev/null; } 2>&1)
    fi
    echo "$TIME_RESULT" > "$OUT_FILE"
}

export -f run_job

# Construire la liste complète des jobs : "BENCH run_id"
JOB_LIST=()
for BENCH in "${!EXE_MAP[@]}"; do
    for (( i=1; i<=NUM_RUNS; i++ )); do
        JOB_LIST+=("$BENCH $i")
    done
done

TOTAL=${#JOB_LIST[@]}
DONE=0

# Lancer les jobs avec un pool de MAX_PARALLEL workers
for JOB in "${JOB_LIST[@]}"; do
    BENCH=$(echo "$JOB" | cut -d' ' -f1)
    RUN_ID=$(echo "$JOB" | cut -d' ' -f2)
    EXE="${EXE_MAP[$BENCH]}"
    OUT_FILE="$TMP_DIR/${BENCH}_run${RUN_ID}.txt"

    # Attendre qu'un slot se libère
    while [ "$(jobs -rp | wc -l)" -ge "$MAX_PARALLEL" ]; do
        sleep 0.05
    done

    run_job "$EXE" "$OUT_FILE" &

    DONE=$(( DONE + 1 ))
    echo -ne "\r[POOL] Jobs lancés: $DONE/$TOTAL — actifs: $(jobs -rp | wc -l)    "
done

# Attendre la fin de tous les workers
wait
echo -e "\r[POOL] Tous les jobs terminés ($TOTAL/$TOTAL).              "
echo "-------------------------------------"

# ==============================================================================
# PHASE 3 : AGRÉGATION DES RÉSULTATS
# ==============================================================================
for BENCH in "${!EXE_MAP[@]}"; do
    CSV_FILE="$OUTPUT_DIR/${BENCH}_results.csv"
    echo "run_id,execution_time" > "$CSV_FILE"
    for (( i=1; i<=NUM_RUNS; i++ )); do
        TIME_RESULT=$(cat "$TMP_DIR/${BENCH}_run${i}.txt" 2>/dev/null)
        echo "$i,$TIME_RESULT" >> "$CSV_FILE"
    done
    echo "[CSV] $BENCH -> $CSV_FILE"
done

# Nettoyage
# rm -rf "$TMP_DIR"

echo "-------------------------------------"
echo "Tests terminés avec succès."