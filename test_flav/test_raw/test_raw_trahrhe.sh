#!/bin/bash

# ==============================================================================
# CONFIGURATION ÉDITABLE
# ==============================================================================

# Liste des benchmarks à tester (correspondant aux noms des dossiers dans pluto_bench/)
BENCHMARKS=("3d7pt" "apop" "game-of-life" "heat-1d" "heat-2d" "heat-3d")

# Paramètres d'exécution
NUM_RUNS=10              # Nombre de répétitions (N)

# Format : Année-Mois-Jour_Heure-Minutes-Secondes
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M")
# Dossier de base pour les résultats
BASE_OUTPUT_DIR="results"
# Concaténation pour créer un dossier unique par exécution
OUTPUT_DIR="${BASE_OUTPUT_DIR}_${TIMESTAMP}"

# Chemins relatifs
PLUTO_BENCH_DIR="/home/marteau/pesto-bench/pluto_bench"
INC_DIR="/home/marteau/pesto-bench/include"
LIB_DIR="/home/marteau/pesto-bench/lib"
LIB_NAME="benchmark"    # Cherchera libbenchmark.a

# Paramètres de compilation
CC="gcc"
CFLAGS="-O3 -I $INC_DIR"
LDFLAGS="-L $LIB_DIR -l$LIB_NAME -lm"

# ==============================================================================
# PRÉPARATION
# ==============================================================================

mkdir -p "$OUTPUT_DIR"

echo "--- Début de la campagne de tests ---"
echo "Nombre de runs par test : $NUM_RUNS"
echo "-------------------------------------"

# ==============================================================================
# BOUCLE PRINCIPALE
# ==============================================================================

for BENCH in "${BENCHMARKS[@]}"; do
    # Détermination du fichier source (gestion des noms différents comme life.c pour game-of-life)
    # On cherche le premier fichier .c dans le dossier
    SRC_DIR="$PLUTO_BENCH_DIR/$BENCH"
    SRC_FILE=$(ls $SRC_DIR/*.c | head -n 1)
    EXE="$SRC_DIR/$BENCH"
    CSV_FILE="$OUTPUT_DIR/${BENCH}_results.csv"

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

    # 2. EXÉCUTION ET CAPTURE DU TEMPS
    echo -n "[2/2] Exécution ($NUM_RUNS fois)... "
    echo "run_id,execution_time" > "$CSV_FILE"

    for (( i=1; i<=$NUM_RUNS; i++ )); do
        # On suppose que le programme affiche le temps sur la sortie standard
        # Sinon, on peut utiliser /usr/bin/time -f "%e"
        TIME_RESULT=$("$EXE" | grep -E "^[0-9.]+$" | tail -n 1)
        
        # Si le binaire ne renvoie pas juste un chiffre, on utilise 'time' système
        if [ -z "$TIME_RESULT" ]; then
            TIME_RESULT=$({ /usr/bin/time -f "%e" "$EXE" > /dev/null; } 2>&1)
        fi

        echo "$i,$TIME_RESULT" >> "$CSV_FILE"
        echo -n "$i "
    done
    
    echo "Terminé. Résultats dans $CSV_FILE"
    echo "-------------------------------------"
    echo "menage $EXE"
    rm -f "$EXE"
done

echo "Tests terminés avec succès."