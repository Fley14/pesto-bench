#!/bin/bash

# 1. Configuration de l'environnement
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date -d '+2 hours' +"%Y-%m-%d-%H-%M-%S")

echo "--- Préparation de la session : $TIMESTAMP ---"
mkdir -p "/home/marteau/test_flav/results/res_$TIMESTAMP"
# ---------------------------------------------------------
# ÉTAPE 1 : Mise à jour de tous les fichiers (Log dynamique)
# ---------------------------------------------------------
echo "Mise à jour des dossiers de résultats..."

for test_script in "$SCRIPT_DIR"/test_*.sh; do
    if [ -f "$test_script" ]; then
        # Explication du sed :
        # 1. On cherche : res_[^/ ]*/
        #    [^/ ]* signifie "n'importe quel caractère sauf un slash ou un espace"
        # 2. On capture le nom du fichier log : \([^ ]*\)
        #    Tout ce qui suit jusqu'à l'espace suivant.
        # 3. On remplace par : res_$TIMESTAMP/\1
        #    \1 est la "référence arrière" qui remet le nom du fichier capturé.

        sed -i "s|res_[^/ ]*/\([^ ]*\)|res_$TIMESTAMP/\1|g" "$test_script"
    fi
done

echo "✅ Dossiers mis à jour (les noms des fichiers .log ont été conservés)."
echo "---------------------------------------------------------"

# ---------------------------------------------------------
# ÉTAPE 2 : Exécution
# ---------------------------------------------------------
echo "Lancement de la suite de tests..."

for test_script in "$SCRIPT_DIR"/test_*.sh; do
    if [ -f "$test_script" ]; then
        script_name=$(basename "$test_script")
        echo "Exécution de $script_name..."
        
        bash "$test_script"
        
        [ $? -eq 0 ] && echo "✅ Succès" || echo "❌ Échec"
        echo "---"
    fi
done

echo "--- Fin de la session ---"