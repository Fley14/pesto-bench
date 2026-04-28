#!/bin/bash

# Configuration
SOURCE_DIR="results_trahrhe/results/res_raw/res_2026-04-28-17-16"
TARGET_DIR="results_valide/results_csv/raw"
STATS_EXECUTABLE="./compute_raw.sh"

# 1. Vérifications
if [ ! -f "$STATS_EXECUTABLE" ]; then
    echo "Erreur : Le script '$STATS_EXECUTABLE' est introuvable."
    exit 1
fi

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Erreur : Le dossier source '$SOURCE_DIR' n'existe pas."
    exit 1
fi

# Création du dossier cible
mkdir -p "$TARGET_DIR"

echo "Début de la conversion des fichiers RAW en statistiques..."
echo "--------------------------------------------------------"

# 2. Parcours récursif des fichiers .csv
find "$SOURCE_DIR" -type f -name "*.csv" | while read -r raw_file; do
    
    # Calcul des chemins
    rel_path="${raw_file#$SOURCE_DIR/}"
    target_subdir=$(dirname "$rel_path")
    filename=$(basename "$raw_file")
    
    # Préparation du dossier de destination spécifique
    dest_path="$TARGET_DIR/$target_subdir"
    mkdir -p "$dest_path"
    
    echo -n "Traitement de : $rel_path ... "
    
    # 3. Exécution du script de calcul
    # On redirige la sortie vers un fichier temporaire pour éviter les conflits
    if "$STATS_EXECUTABLE" "$raw_file" > /dev/null 2>&1; then
        # Le script compute_stats.sh génère "stats_result.csv"
        if [ -f "stats_result.csv" ]; then
            mv "stats_result.csv" "$dest_path/$filename"
            echo "OK"
        fi
    else
        echo "ÉCHEC"
    fi
done

echo "--------------------------------------------------------"
echo "Traitement terminé. Les résultats sont dans : $TARGET_DIR"