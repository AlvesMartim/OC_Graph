from .llm import init_gemini, generate_score_function
from .prompt import build_initial_prompt, build_iteration_prompt
from .evaluator import evaluate, EVAL_SUBSET_SIZE

N_ITERATIONS = 10
TOP_K = 3


def run_funsearch(benchmark_df):
    print("Initialisation du modèle Gemini...")
    client = init_gemini()

    best_functions = []  # liste de (code, nb_solved, cost, details)
    all_failed = set()

    for iteration in range(1, N_ITERATIONS + 1):
        print(f"\n{'='*60}")
        print(f"FUNSEARCH — Itération {iteration}/{N_ITERATIONS}")
        print(f"{'='*60}")

        if not best_functions:
            prompt = build_initial_prompt()
        else:
            # Conjectures jamais réfutées par aucune fonction
            all_solved = set(cid for _, _, _, d in best_functions for cid in d.get('solved', []))
            all_failed = set(cid for _, _, _, d in best_functions for cid in d.get('failed', [])) - all_solved
            
            # Format attendu par le prompt builder
            prompt_best_functions = [(code, nb_solved, details) for code, nb_solved, cost, details in best_functions[:TOP_K]]
            prompt = build_iteration_prompt(prompt_best_functions, failed_conjectures=list(all_failed))

        print("Génération d'une nouvelle fonction de score par le LLM...")
        code = generate_score_function(client, prompt)

        if code is None:
            print("Le LLM n'a pas produit de code valide, itération ignorée.")
            continue

        print(f"\nFonction générée :\n{'-'*40}\n{code}\n{'-'*40}")

        print(f"\nÉvaluation sur {EVAL_SUBSET_SIZE} conjectures (max 60s chacune)...")
        nb_solved, details = evaluate(code, benchmark_df)
        cost = details.get('cost', float('inf'))
        
        print(f"\nPerformance : {nb_solved}/{EVAL_SUBSET_SIZE} conjectures réfutées")
        print(f"Coût total : {cost:.1f}")
        print(f"  Réfutées : {details['solved']}")
        print(f"  Échouées : {details['failed']}")

        best_functions.append((code, nb_solved, cost, details))
        # On trie d'abord par le coût (le plus faible est le meilleur), puis par le nombre de conjectures résolues (le plus élevé est le meilleur)
        best_functions.sort(key=lambda x: x[2])
        best_functions = best_functions[:TOP_K]

        print(f"\nTop {TOP_K} actuel :")
        for rank, (_, solved, c, _) in enumerate(best_functions, start=1):
            print(f"  #{rank} : Coût {c:.1f} ({solved}/{EVAL_SUBSET_SIZE} réfutées)")

    if best_functions:
        best_code, best_perf_solved, best_cost, _ = best_functions[0]
        print(f"\n{'='*60}")
        print(f"Meilleure fonction trouvée (Coût: {best_cost:.1f}, Réfutées: {best_perf_solved}/{EVAL_SUBSET_SIZE}) :")
        print(f"{'-'*40}\n{best_code}\n{'-'*40}")
        return best_code, best_perf_solved

    return None, 0
