#!/bin/bash

# ==============================================================================
# CONFIGURATION DES DESTINATIONS (SCP)
# ==============================================================================
REMOTE_SOURCE="trahrhe:/home/marteau/test_flav/results/"
LOCAL_BASE_DIR="./results_trahrhe"

# Gestion de l'argument pour le sous-dossier
if [ -z "$1" ]; then
    # Pas d'argument : dossier racine
    TARGET_DIR="$LOCAL_BASE_DIR"
else
    # Argument présent : création d'un sous-dossier spécifique
    TARGET_DIR="$LOCAL_BASE_DIR/$1"
fi

# Création du dossier cible si nécessaire
mkdir -p "$TARGET_DIR"

# ==============================================================================
# RÉCUPÉRATION DES DONNÉES (SCP)
# ==============================================================================
echo "--- Récupération des résultats depuis trahrhe ---"
echo "Source : $REMOTE_SOURCE"
echo "Destination : $TARGET_DIR"

scp -r $REMOTE_SOURCE "$TARGET_DIR"

if [ $? -eq 0 ]; then
    echo "Succès : Fichiers récupérés."
else
    echo "Erreur : Échec du transfert SCP."
    exit 1
fi