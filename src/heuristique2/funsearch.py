import os

from .llm import init_gemini, generate_score_function
from .prompt import build_initial_prompt, build_iteration_prompt
from .evaluator import evaluate, EVAL_SUBSET_SIZE

N_ITERATIONS = 1000  # Infinite loop conceptually, stopped by user
TOP_K = 8

def save_best(code, cost):
    path = os.path.join(os.path.dirname(__file__), 'best_score_function.py')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# Cost: {cost:.1f}\n")
        f.write(code)
    print(f"-> best_score_function.py mis à jour (Coût: {cost:.1f})")

def load_best():
    path = os.path.join(os.path.dirname(__file__), 'best_score_function.py')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines and lines[0].startswith("# Cost:"):
                return "".join(lines[1:]).strip()
            return "".join(lines).strip()
    return None

def is_valid_function(code):
    """Vérifie que le code compile."""
    if not code:
        return False
    try:
        compile(code, '<string>', 'exec')
        return True
    except Exception:
        return False

def run_funsearch(benchmark_df):
    print("Initialisation du modèle Gemini...")
    client = init_gemini()

    population = []  # list of (code, nb_solved, cost, details)

    print("--- Étape 1 : Initialisation ---")
    candidates = []
    
    # 1. Fonction basique
    baseline_code = """def heuristic_score(G, invariants, conjecture):
    violation = conjecture.violation(invariants)
    return violation"""
    candidates.append(("Baseline", baseline_code))
    
    # 2. Meilleur existant
    best_known_code = load_best()
    if best_known_code and is_valid_function(best_known_code):
        candidates.append(("Meilleur existant", best_known_code))
    
    # 3. Demander au LLM des fonctions initiales
    prompt_init = build_initial_prompt()
    for i in range(3):
        print(f"Demande de fonction initiale au LLM ({i+1}/3)...")
        llm_code = generate_score_function(client, prompt_init)
        if llm_code and is_valid_function(llm_code):
             print(f"\n--- Fonction générée (LLM Init {i+1}) ---\n{llm_code}\n-----------------------------------\n")
             candidates.append((f"LLM Init {i+1}", llm_code))
        else:
             print("Le LLM n'a pas produit de code valide.")
    
    print(f"Évaluation de {len(candidates)} fonctions de score initiales...")
    for name, code in candidates:
        solved, details = evaluate(code, benchmark_df)
        cost = details['cost']
        print(f"[{name}] Réfutées: {solved}/{EVAL_SUBSET_SIZE}, Coût: {cost:.1f}")
        population.append((code, solved, cost, details))
        
    population.sort(key=lambda x: x[2])
    population = population[:TOP_K]
    
    if best_known_code is None or population[0][0] != best_known_code:
        save_best(population[0][0], population[0][2])

    print("--- Étape 2 : Boucle infinie ---")
    for iteration in range(1, N_ITERATIONS + 1):
        print(f"\n{'='*60}")
        print(f"FUNSEARCH — Itération {iteration}/{N_ITERATIONS}")
        print(f"{'='*60}")
        
        new_candidates = []

        # Mécanisme 1 : LLM génère de nouvelles fonctions en se basant sur les meilleures
        prompt_best = [(c, s, d) for c, s, cost, d in population[:3]]
        prompt = build_iteration_prompt(prompt_best)
        
        # On demande au LLM de générer 3 nouvelles fonctions pour explorer différentes directions
        for i in range(3):
            print(f"Génération de variante LLM ({i+1}/3)...")
            llm_code = generate_score_function(client, prompt)
            if llm_code and is_valid_function(llm_code):
                print(f"\n--- Variante générée (LLM Var {i+1}) ---\n{llm_code}\n----------------------------------\n")
                new_candidates.append((f"LLM Var {i+1}", llm_code))
            else:
                print("Le LLM n'a pas produit de code valide.")

        print(f"\nÉvaluation de {len(new_candidates)} nouveaux candidats...")
        for name, code in new_candidates:
            solved, details = evaluate(code, benchmark_df)
            cost = details['cost']
            print(f"[{name}] Réfutées: {solved}/{EVAL_SUBSET_SIZE}, Coût: {cost:.1f}")
            population.append((code, solved, cost, details))
            
        # Sélection
        population.sort(key=lambda x: x[2])
        best_cost_so_far = population[0][2]
        population = population[:TOP_K]
        
        # Sauvegarde si on a un nouveau meilleur global
        best_saved_code = load_best()
        if best_saved_code:
            if best_saved_code != population[0][0]:
                save_best(population[0][0], population[0][2])
        else:
            save_best(population[0][0], population[0][2])

        print(f"\nTop {min(3, len(population))} actuel :")
        for rank, (_, solved, c, _) in enumerate(population[:3], start=1):
            print(f"  #{rank} : Coût {c:.1f} ({solved}/{EVAL_SUBSET_SIZE} réfutées)")

    best_code, best_perf_solved, best_cost, _ = population[0]
    return best_code, best_perf_solved
