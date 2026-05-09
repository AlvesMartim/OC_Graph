from .llm import init_gemini, generate_score_function
from .prompt import build_initial_prompt, build_iteration_prompt
from .evaluator import evaluate

# Nombre d'itérations de la boucle FunSearch
N_ITERATIONS = 5
# Nombre de meilleures fonctions conservées et renvoyées au LLM
TOP_K = 3


def run_funsearch(benchmark_df):
    """
    Boucle principale FunSearch :
    1. LLM génère une fonction de score
    2. On l'évalue sur un sous-ensemble du benchmark
    3. On garde les meilleures
    4. On renvoie les meilleures au LLM pour la prochaine itération
    """
    print("Initialisation du modèle Gemini...")
    model = init_gemini()

    best_functions = []  # liste de (code, performance)

    for iteration in range(1, N_ITERATIONS + 1):
        print(f"\n{'='*60}")
        print(f"FUNSEARCH — Itération {iteration}/{N_ITERATIONS}")
        print(f"{'='*60}")

        # Construction du prompt
        if not best_functions:
            prompt = build_initial_prompt()
        else:
            prompt = build_iteration_prompt(best_functions[:TOP_K])

        # Génération de la fonction par le LLM
        print("Génération d'une nouvelle fonction de score par le LLM...")
        code = generate_score_function(model, prompt)

        if code is None:
            print("Le LLM n'a pas produit de code valide, itération ignorée.")
            continue

        print(f"\nFonction générée :\n{'-'*40}\n{code}\n{'-'*40}")

        # Évaluation sur le benchmark
        print(f"\nÉvaluation sur {20} conjectures (max 10s chacune)...")
        perf = evaluate(code, benchmark_df)
        print(f"\nPerformance : {perf}/20 conjectures réfutées")

        # Mise à jour du classement
        best_functions.append((code, perf))
        best_functions.sort(key=lambda x: x[1], reverse=True)
        best_functions = best_functions[:TOP_K]

        print(f"\nTop {TOP_K} actuel :")
        for rank, (_, p) in enumerate(best_functions, start=1):
            print(f"  #{rank} : {p}/20 conjectures réfutées")

    # Résultat final
    if best_functions:
        best_code, best_perf = best_functions[0]
        print(f"\n{'='*60}")
        print(f"Meilleure fonction trouvée ({best_perf}/20 conjectures réfutées) :")
        print(f"{'-'*40}\n{best_code}\n{'-'*40}")
        return best_code, best_perf

    return None, 0
