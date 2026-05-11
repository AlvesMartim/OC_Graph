import json
import os
import sys
from datetime import datetime

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
    results = []

    for processed, (_, conjecture_row) in enumerate(benchmark_df.iterrows(), start=1):
        cid = conjecture_row['Conjecture ID']
        print(f"--- Conjecture {cid}: {conjecture_row['Conjecture']} ---")

        result, elapsed, info = run_heuristic(conjecture_row)
        total_time += elapsed

        if result is not None:
            found += 1
            results.append({
                "conjecture_id": int(cid),
                "conjecture": conjecture_row['Conjecture'],
                "counter_example": info,
            })
        else:
            print(f"Aucun contre-exemple trouvé (pénalité : 120s)\n")
            results.append({
                "conjecture_id": int(cid),
                "conjecture": conjecture_row['Conjecture'],
                "counter_example": None,
            })

        print(f">> Progression : {found}/{processed} contre-exemples trouvés\n")

    failures = total - found
    score = total_time

    print("=" * 60)
    print(f"Résultats   : {found}/{total} conjectures réfutées")
    print(f"Temps moyen : {total_time / total:.1f}s")
    print(f"Score total : {score:.1f}s  ({found} réfutées × temps réel + {failures} échecs × 120s)")
    print(f"             (plus bas = meilleur, minimum théorique = 0s)")
    print("=" * 60)

    # Écriture du JSON
    output = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "conjectures_refutees": found,
        "total_conjectures": total,
        "score_total_s": round(score, 3),
        "results": results,
    }
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'benchmark')
    output_path = os.path.join(output_dir, 'results.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nRésultats exportés dans : {output_path}")