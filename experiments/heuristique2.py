
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Ajouter la racine du projet au PYTHONPATH pour pouvoir importer src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from src.heuristique2 import run_funsearch

if __name__ == '__main__':
    benchmark_path = os.path.join(os.path.dirname(__file__), '..', 'benchmark', 'benchmark.xlsx')
    try:
        benchmark_df = pd.read_excel(benchmark_path)
        print(f"{len(benchmark_df)} conjectures chargées.\n")
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{benchmark_path}' est introuvable.")
        exit()

    best_code, best_perf = run_funsearch(benchmark_df)

    if best_code:
        print(f"\nFunSearch terminé. Meilleur nombre de conjectures réfutées : {best_perf}")
        print("Tu peux copier la fonction ci-dessus et l'utiliser comme nouvelle heuristique.")
    else:
        print("\nAucune fonction valide trouvée.")