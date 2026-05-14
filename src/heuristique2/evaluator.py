import random
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd
import ast

from src.heuristique1.invariants import compute_invariants
from src.heuristique1.repair import repair_if_needed
from src.heuristique1.search import generate_initial_graphs, select_candidate, violation_score, targeted_mutate

EVAL_TIME_LIMIT = 60
EVAL_SUBSET_SIZE = 100

class ConjectureWrapper:
    def __init__(self, conjecture_dict):
        self.conjecture_dict = conjecture_dict

    def violation(self, invariants):
        return violation_score(invariants, self.conjecture_dict)

def load_heuristic_score(code):
    namespace = {}
    try:
        # Avoid import errors within the exec scope by providing a safe global
        exec(code, {'abs': abs}, namespace)
        return namespace.get('heuristic_score', None)
    except Exception as e:
        print(f"[Evaluator] Erreur chargement fonction de score: {e}")
    return None

def _search_with_heuristic(conjecture_tuple, score_code, time_limit=EVAL_TIME_LIMIT):
    heuristic_score_fn = load_heuristic_score(score_code)
    conjecture = pd.Series(conjecture_tuple[1]).to_dict()
    cid = conjecture['Conjecture ID']
    
    # Define needed invariants to compute
    needed = {conjecture.get('X'), conjecture.get('Y')} - {None}
    # Pre-compute names needed by the heuristic
    needed.update({"n", "m", "delta", "Delta", "diam", "gamma", "alpha", "tau", "triangles"})

    if heuristic_score_fn is None:
        return False, time_limit, cid

    start = time.time()
    
    subgroup_str = conjecture.get('Subgroup', '')

    population = generate_initial_graphs(conjecture)
    scored_pop = []
    
    wrapper = ConjectureWrapper(conjecture)

    for G in population:
        inv = compute_invariants(G, needed=needed)
        v_score = violation_score(inv, conjecture)
        if v_score > 0:
            return True, time.time() - start, cid
        
        try:
            h_score = heuristic_score_fn(G, inv, wrapper)
        except Exception:
            h_score = v_score
            
        scored_pop.append((G, h_score, v_score))

    scored_pop.sort(key=lambda x: x[1], reverse=True)
    scored_pop = scored_pop[:10]
    stagnation = 0

    while time.time() - start < time_limit:
        k = min(3, len(scored_pop))
        tournament = random.sample(scored_pop, k)
        G = max(tournament, key=lambda x: x[1])[0]
        
        H = targeted_mutate(G, conjecture)

        if subgroup_str:
            H = repair_if_needed(H, subgroup_str)

        if H.number_of_nodes() < 2:
            stagnation += 1
            continue

        inv = compute_invariants(H, needed=needed)
        v_score = violation_score(inv, conjecture)
        
        if v_score > 0:
            return True, time.time() - start, cid
            
        try:
            h_score = heuristic_score_fn(H, inv, wrapper)
        except Exception:
            h_score = v_score

        best = scored_pop[0][1] if scored_pop else -float('inf')
        if h_score > best:
            stagnation = 0
            scored_pop.append((H, h_score, v_score))
            scored_pop.sort(key=lambda x: x[1], reverse=True)
            scored_pop = scored_pop[:10]
        else:
            stagnation += 1

        if stagnation > 200:
            for G_new in generate_initial_graphs(conjecture, num_graphs=3):
                inv_new = compute_invariants(G_new, needed=needed)
                v_new = violation_score(inv_new, conjecture)
                if v_new > 0:
                    return True, time.time() - start, cid
                try:
                    h_new = heuristic_score_fn(G_new, inv_new, wrapper)
                except Exception:
                    h_new = v_new
                scored_pop.append((G_new, h_new, v_new))
            scored_pop.sort(key=lambda x: x[1], reverse=True)
            scored_pop = scored_pop[:10]
            stagnation = 0

    return False, time_limit, cid

def evaluate(score_code, benchmark_df, subset_size=EVAL_SUBSET_SIZE):
    heuristic_score_fn = load_heuristic_score(score_code)
    if heuristic_score_fn is None:
        print("[Evaluator] Erreur: Fonction de score invalide, évaluation annulée.")
        return 0, {'solved': [], 'failed': [], 'cost': 120 * subset_size}

    subset = benchmark_df.head(subset_size)
    solved, failed = [], []
    total_cost = 0

    tasks = [(row_tuple, score_code) for row_tuple in subset.iterrows()]
    print(f"  - Lancement de {len(tasks)} tâches d'évaluation en parallèle...")

    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(_search_with_heuristic, task[0], task[1]): task[0][1]['Conjecture ID'] for task in tasks}
        
        for future in as_completed(futures):
            cid = futures[future]
            try:
                success, elapsed, res_cid = future.result()

                if success:
                    status = "OK"
                    solved.append(res_cid)
                    cost = elapsed
                else:
                    status = "--"
                    failed.append(res_cid)
                    cost = 120
                    
                total_cost += cost
                print(f"    [{status}] Conjecture {res_cid} ({elapsed:.1f}s) -> Coût: {cost:.1f}")

            except Exception as e:
                print(f"    [ERREUR] La tâche pour la conjecture {cid} a échoué : {e}")
                failed.append(cid)
                total_cost += 120

    return len(solved), {'solved': sorted(solved), 'failed': sorted(failed), 'cost': total_cost}
