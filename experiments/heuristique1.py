import os
import sys

# Ajouter la racine du projet au PYTHONPATH pour pouvoir importer src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from src.heuristique1 import run_heuristic

if __name__ == '__main__':
    benchmark_path = os.path.join(os.path.dirname(__file__), '..', 'benchmark', 'benchmark.xlsx')
    try:
        benchmark_df = pd.read_excel(benchmark_path)
        print(f"{len(benchmark_df)} conjectures chargées.\n")
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{benchmark_path}' est introuvable.")
        exit()

    total = len(benchmark_df)
    found = 0
    total_time = 0.0

    for processed, (_, conjecture_row) in enumerate(benchmark_df.iterrows(), start=1):
        cid = conjecture_row['Conjecture ID']
        print(f"--- Conjecture {cid}: {conjecture_row['Conjecture']} ---")

        result, elapsed = run_heuristic(conjecture_row)
        total_time += elapsed

        if result is not None:
            found += 1
        else:
            print(f"Aucun contre-exemple trouvé (pénalité : 120s)\n")

        print(f">> Progression : {found}/{processed} contre-exemples trouvés\n")

    failures = total - found
    score = total_time  # succès = temps réel, échecs = 60s chacun

    print("=" * 60)
    print(f"Résultats   : {found}/{total} conjectures réfutées")
    print(f"Temps moyen : {total_time / total:.1f}s")
    print(f"Score total : {score:.1f}s  ({found} réfutées × temps réel + {failures} échecs × 120s)")
    print(f"             (plus bas = meilleur, minimum théorique = 0s)")
    print("=" * 60)