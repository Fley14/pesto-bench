SOURCE_ROOT="results_valide/logs"
TARGET_ROOT="results_valide/results_csv"
 
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARSE_SCRIPT="$SCRIPT_DIR/extract_best_run.py"
 
find "$SOURCE_ROOT" -type f -name "*.log" | while read -r log_file; do
    # Chemin relatif par rapport à SOURCE_ROOT
    rel_path="${log_file#$SOURCE_ROOT/}"
 
    # Chemin de sortie : même arborescence, extension .csv
    csv_file="$TARGET_ROOT/${rel_path%.log}.csv"
 
    # Créer le dossier cible si besoin
    mkdir -p "$(dirname "$csv_file")"
 
    # Parser le log
    if python3 "$PARSE_SCRIPT" "$log_file" > "$csv_file"; then
        echo "[OK]    $log_file -> $csv_file"
    else
        echo "[SKIP]  $log_file (pas de best run)"
        rm -f "$csv_file"
    fi
done
