import random
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd

from src.heuristique1.invariants import compute_invariants
from src.heuristique1.repair import repair_if_needed
from src.heuristique1.search import generate_initial_graphs, select_candidate, mutate

# Durée max par conjecture lors de l'évaluation
EVAL_TIME_LIMIT = 60
# Taille du sous-ensemble de conjectures pour l'évaluation
EVAL_SUBSET_SIZE = 25


def load_score_function(code):
    """Compile et retourne la fonction score depuis le code Python fourni, ou None si invalide."""
    namespace = {}
    try:
        exec(compile(code, '<llm_score>', 'exec'), namespace)
        fn = namespace.get('heuristic_score')
        if callable(fn):
            return fn
    except Exception as e:
        print(f"[Evaluator] Fonction invalide : {e}")
    return None


def _search_with_score(conjecture_tuple, score_fn_code, time_limit=EVAL_TIME_LIMIT):
    """
    Wrapper pour la recherche locale, conçu pour être exécuté dans un processus séparé.
    Prend un tuple de conjecture et le code de la fonction de score pour éviter les problèmes de pickling.
    """
    # Re-créer la fonction de score dans le processus enfant
    score_fn = load_score_function(score_fn_code)
    if score_fn is None:
        return False, time_limit, conjecture_tuple[0] # Conjecture ID

    conjecture = pd.Series(conjecture_tuple[1]).to_dict()
    cid = conjecture['Conjecture ID']
    start = time.time()
    graph_class = conjecture.get('Subgroup')

    population = generate_initial_graphs(conjecture)
    scored_pop = []
    for G in population:
        inv = compute_invariants(G)
        try:
            s = float(score_fn(G, inv, conjecture))
        except Exception:
            s = -float('inf')
            
        # La condition de succès est généralement testée par rapport à la conjecture directement
        # mais ici on assume que le score reflète la violation si > 0 pour l'exemple (à voir avec votre projet)
        try:
           from fractions import Fraction
           import ast
           X_val = float(inv.get(conjecture['X'], 0))
           Y_val = float(inv.get(conjecture['Y'], 0))
           coeffs_raw = conjecture.get('Coefficients', '')
           intercept_raw = str(conjecture.get('Intercept', 0))
           try:
               coeffs = ast.literal_eval(coeffs_raw) if isinstance(coeffs_raw, str) else coeffs_raw
               intercept = float(Fraction(intercept_raw))
               f_X = intercept + sum(float(Fraction(c)) * (X_val ** (i + 1)) for i, c in enumerate(coeffs))
           except Exception:
               f_X = float(conjecture.get('Degree', 1)) * X_val
           if conjecture['Sign'] in ('<=', '<'):
               violation = Y_val - f_X
           else:
               violation = f_X - Y_val
               
           if violation > 0:
               return True, time.time() - start, cid
        except Exception:
            pass

        scored_pop.append((G, s))

    scored_pop.sort(key=lambda x: x[1], reverse=True)
    scored_pop = scored_pop[:10]
    stagnation = 0

    while time.time() - start < time_limit:
        G = select_candidate(scored_pop)
        H = mutate(G)

        if graph_class:
            H = repair_if_needed(H, graph_class)

        if H.number_of_nodes() < 2:
            continue

        inv = compute_invariants(H)
        try:
            s = float(score_fn(H, inv, conjecture))
        except Exception:
            s = -float('inf')

        try:
           X_val = float(inv.get(conjecture['X'], 0))
           Y_val = float(inv.get(conjecture['Y'], 0))
           try:
               f_X = intercept + sum(float(Fraction(c)) * (X_val ** (i + 1)) for i, c in enumerate(coeffs))
           except Exception:
               f_X = float(conjecture.get('Degree', 1)) * X_val
           if conjecture['Sign'] in ('<=', '<'):
               violation = Y_val - f_X
           else:
               violation = f_X - Y_val
               
           if violation > 0:
               return True, time.time() - start, cid
        except Exception:
            pass

        best = scored_pop[0][1] if scored_pop else -float('inf')
        if s > best:
            stagnation = 0
            scored_pop.append((H, s))
            scored_pop.sort(key=lambda x: x[1], reverse=True)
            scored_pop = scored_pop[:10]
        else:
            stagnation += 1

        if stagnation > 200:
            for G_new in generate_initial_graphs(conjecture, num_graphs=3):
                inv_new = compute_invariants(G_new)
                try:
                    s_new = float(score_fn(G_new, inv_new, conjecture))
                except Exception:
                    s_new = -float('inf')
                
                try:
                   X_val = float(inv_new.get(conjecture['X'], 0))
                   Y_val = float(inv_new.get(conjecture['Y'], 0))
                   try:
                       f_X = intercept + sum(float(Fraction(c)) * (X_val ** (i + 1)) for i, c in enumerate(coeffs))
                   except Exception:
                       f_X = float(conjecture.get('Degree', 1)) * X_val
                   if conjecture['Sign'] in ('<=', '<'):
                       violation = Y_val - f_X
                   else:
                       violation = f_X - Y_val
                       
                   if violation > 0:
                       return True, time.time() - start, cid
                except Exception:
                    pass

                scored_pop.append((G_new, s_new))
            scored_pop.sort(key=lambda x: x[1], reverse=True)
            scored_pop = scored_pop[:10]
            stagnation = 0

    return False, time_limit, cid


def evaluate(code, benchmark_df, subset_size=EVAL_SUBSET_SIZE):
    """
    Évalue une fonction de score sur un sous-ensemble aléatoire du benchmark en parallèle.
    Retourne (nb_réfutées, details) où details = {'solved': [...], 'failed': [...]}.
    La métrique de performance devient maintenant le "coût" (somme des temps).
    """
    score_fn = load_score_function(code)
    if score_fn is None:
        return 0, {'solved': [], 'failed': [], 'cost': 120 * subset_size}

    subset = benchmark_df.sample(n=min(subset_size, len(benchmark_df)), random_state=random.randint(0, 9999))
    solved, failed = [], []
    total_cost = 0

    tasks = [(row_tuple, code) for row_tuple in subset.iterrows()]

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(_search_with_score, task[0], task[1]) for task in tasks]
        
        for future in as_completed(futures):
            try:
                success, elapsed, cid = future.result()
                
                if success:
                    status = "OK"
                    solved.append(cid)
                    cost = elapsed
                else:
                    status = "--"
                    failed.append(cid)
                    cost = 120 # Pénalité de non-réfutation
                    
                total_cost += cost
                print(f"  [{status}] Conjecture {cid} ({elapsed:.1f}s) -> Cost: {cost:.1f}")
                
            except Exception as e:
                print(f"Une erreur est survenue dans un processus enfant : {e}")

    return len(solved), {'solved': sorted(solved), 'failed': sorted(failed), 'cost': total_cost}