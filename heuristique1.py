import pandas as pd

from heuristique1 import run_heuristic

if __name__ == '__main__':
    try:
        benchmark_df = pd.read_excel("benchmark.xlsx")
        print(f"{len(benchmark_df)} conjectures chargées.\n")
    except FileNotFoundError:
        print("Erreur : Le fichier 'benchmark.xlsx' est introuvable.")
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
            print(f"Aucun contre-exemple trouvé (60.00s écoulées)\n")

        print(f">> Progression : {found}/{processed} contre-exemples trouvés\n")

    print("=" * 60)
    print(f"Résultats : {found}/{total} conjectures réfutées")
    print(f"Temps total : {total_time:.1f}s  |  Temps moyen : {total_time / total:.1f}s")
    print("=" * 60)
