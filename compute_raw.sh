#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <input_raw.csv>"
    exit 1
fi

INPUT=$1
OUTPUT="stats_result.csv"

# On utilise awk pour traiter les calculs
awk -F',' '
BEGIN {
    # Initialisation de l en-tête
    print "T0,T1,T2,T3,score,Trimmed Mean,STD Dev,STD Dev %"
}
NR > 1 {
    val[count++] = $2
    sum += $2
    sumsq += $2 * $2
    if (NR == 2 || $2 < min) min = $2
    if (NR == 2 || $2 > max) max = $2
}
END {
    if (count == 0) exit;

    # 1. Score (Min)
    score = min

    # 2. Trimmed Mean (on retire une fois le min et une fois le max)
    if (count > 2) {
        t_mean = (sum - min - max) / (count - 2)
    } else {
        t_mean = sum / count
    }

    # 3. Standard Deviation
    mean = sum / count
    variance = (sumsq / count) - (mean * mean)
    std_dev = sqrt(variance < 0 ? 0 : variance)

    # 4. Standard Deviation %
    std_dev_perc = (mean > 0) ? (std_dev / mean) * 100 : 0

    # Affichage avec T0,T1,T2,T3 fixés à 1
    printf "1,1,1,1,%.6f,%.6f,%.6f,%.2f\n", score, t_mean, std_dev, std_dev_perc
}' "$INPUT" > "$OUTPUT"

echo "Statistiques générées dans $OUTPUT"