#!/bin/bash

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# Dossier source (où sont les CSV)
INPUT_DIR=${1:-"./results_trahrhe/results_raw"}

# Dossier de destination (où seront les stats)
OUTPUT_BASE_DIR="./results_trahrhe/results_raw/stats"

echo "--- Début du traitement récursif ---"
echo "Source : $INPUT_DIR"
echo "Destination : $OUTPUT_BASE_DIR"
echo "------------------------------------"

# ==============================================================================
# TRAITEMENT
# ==============================================================================

# On utilise 'find' pour lister tous les fichiers .csv récursivement
find "$INPUT_DIR" -type f -name "*.csv" | while read -r csv_path; do
    
    # 1. Déterminer le chemin relatif par rapport à l'entrée
    # (Ex: si csv_path est ./res/v1/test.csv, rel_path est v1/test.csv)
    rel_path="${csv_path#$INPUT_DIR/}"
    rel_dir=$(dirname "$rel_path")
    filename=$(basename "$csv_path")
    
    # 2. Créer le dossier de destination correspondant
    dest_dir="$OUTPUT_BASE_DIR/$rel_dir"
    mkdir -p "$dest_dir"
    
    # 3. Définir le nom du fichier de sortie
    output_file="$dest_dir/${filename%.csv}.stats"

    # 4. Calculer les stats et écrire dans le fichier
    awk -F',' '
    NR > 1 {
        val = $2
        sum += val
        sumsq += val*val
        if(n==0) {min=max=val}
        if(val<min) min=val
        if(val>max) max=val
        n++
    }
    END {
        if (n > 0) {
            avg = sum / n
            # Écart-type (population)
            std = sqrt((sumsq / n) - (avg * avg))
            
            print "--- Statistiques pour : " fname " ---"
            print "Nombre d échantillons : " n
            print "--------------------------------------"
            printf "Moyenne    : %.4f\n", avg
            printf "Écart-type : %.4f\n", std
            printf "Minimum    : %.4f\n", min
            printf "Maximum    : %.4f\n", max
            print "--------------------------------------"
        }
    }' fname="$filename" "$csv_path" > "$output_file"

    echo "Traité : $rel_path -> $output_file"
done

echo "------------------------------------"
echo "Terminé. Toutes les stats sont dans : $OUTPUT_BASE_DIR"