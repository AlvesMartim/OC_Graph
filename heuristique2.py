from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from heuristique2 import run_funsearch

if __name__ == '__main__':
    try:
        benchmark_df = pd.read_excel("benchmark.xlsx")
        print(f"{len(benchmark_df)} conjectures chargées.\n")
    except FileNotFoundError:
        print("Erreur : Le fichier 'benchmark.xlsx' est introuvable.")
        exit()

    best_code, best_perf = run_funsearch(benchmark_df)

    if best_code:
        print(f"\nFunSearch terminé. Meilleur nombre de conjectures réfutées : {best_perf}")
        print("Tu peux copier la fonction ci-dessus et l'utiliser comme nouvelle heuristique.")
    else:
        print("\nAucune fonction valide trouvée.")