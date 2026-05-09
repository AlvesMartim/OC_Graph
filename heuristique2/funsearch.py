from .llm import init_gemini, generate_score_function
from .prompt import build_initial_prompt, build_iteration_prompt
from .evaluator import evaluate, EVAL_SUBSET_SIZE

N_ITERATIONS = 5
TOP_K = 3


def run_funsearch(benchmark_df):
    print("Initialisation du modèle Gemini...")
    client = init_gemini()

    best_functions = []  # liste de (code, perf, details)
    all_failed = set()

    for iteration in range(1, N_ITERATIONS + 1):
        print(f"\n{'='*60}")
        print(f"FUNSEARCH — Itération {iteration}/{N_ITERATIONS}")
        print(f"{'='*60}")

        if not best_functions:
            prompt = build_initial_prompt()
        else:
            # Conjectures jamais réfutées par aucune fonction
            all_solved = set(cid for _, _, d in best_functions for cid in d.get('solved', []))
            all_failed = set(cid for _, _, d in best_functions for cid in d.get('failed', [])) - all_solved
            prompt = build_iteration_prompt(best_functions[:TOP_K], failed_conjectures=list(all_failed))

        print("Génération d'une nouvelle fonction de score par le LLM...")
        code = generate_score_function(client, prompt)

        if code is None:
            print("Le LLM n'a pas produit de code valide, itération ignorée.")
            continue

        print(f"\nFonction générée :\n{'-'*40}\n{code}\n{'-'*40}")

        print(f"\nÉvaluation sur {EVAL_SUBSET_SIZE} conjectures (max 10s chacune)...")
        perf, details = evaluate(code, benchmark_df)
        print(f"\nPerformance : {perf}/{EVAL_SUBSET_SIZE} conjectures réfutées")
        print(f"  Réfutées : {details['solved']}")
        print(f"  Échouées : {details['failed']}")

        best_functions.append((code, perf, details))
        best_functions.sort(key=lambda x: x[1], reverse=True)
        best_functions = best_functions[:TOP_K]

        print(f"\nTop {TOP_K} actuel :")
        for rank, (_, p, _d) in enumerate(best_functions, start=1):
            print(f"  #{rank} : {p}/{EVAL_SUBSET_SIZE} conjectures réfutées")

    if best_functions:
        best_code, best_perf, _ = best_functions[0]
        print(f"\n{'='*60}")
        print(f"Meilleure fonction trouvée ({best_perf}/{EVAL_SUBSET_SIZE} conjectures réfutées) :")
        print(f"{'-'*40}\n{best_code}\n{'-'*40}")
        return best_code, best_perf

    return None, 0
