import random
import time

import networkx as nx

from heuristique1.invariants import compute_invariants
from heuristique1.repair import repair_if_needed
from heuristique1.search import generate_initial_graphs, select_candidate, mutate

# Durée max par conjecture lors de l'évaluation (plus courte qu'en production)
EVAL_TIME_LIMIT = 10
EVAL_SUBSET_SIZE = 20


def load_score_function(code):
    """Compile et retourne la fonction score depuis le code Python fourni, ou None si invalide."""
    namespace = {}
    try:
        exec(compile(code, '<llm_score>', 'exec'), namespace)
        fn = namespace.get('score')
        if callable(fn):
            return fn
    except Exception as e:
        print(f"[Evaluator] Fonction invalide : {e}")
    return None


def _search_with_score(conjecture, score_fn, time_limit=EVAL_TIME_LIMIT):
    """Recherche locale avec une fonction de score personnalisée."""
    start = time.time()
    graph_class = conjecture.get('Subgroup')

    population = generate_initial_graphs(conjecture)

    scored_pop = []
    for G in population:
        inv = compute_invariants(G)
        try:
            s = float(score_fn(inv, conjecture))
        except Exception:
            s = -float('inf')
        if s > 0:
            return True, time.time() - start
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
            s = float(score_fn(inv, conjecture))
        except Exception:
            s = -float('inf')

        if s > 0:
            return True, time.time() - start

        best = scored_pop[0][1]
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
                    s_new = float(score_fn(inv_new, conjecture))
                except Exception:
                    s_new = -float('inf')
                if s_new > 0:
                    return True, time.time() - start
                scored_pop.append((G_new, s_new))
            scored_pop.sort(key=lambda x: x[1], reverse=True)
            scored_pop = scored_pop[:10]
            stagnation = 0

    return False, time_limit


def evaluate(code, benchmark_df, subset_size=EVAL_SUBSET_SIZE):
    """
    Évalue une fonction de score sur un sous-ensemble aléatoire du benchmark.
    Retourne (nb_réfutées, details) où details = {'solved': [...], 'failed': [...]}.
    """
    score_fn = load_score_function(code)
    if score_fn is None:
        return 0, {'solved': [], 'failed': []}

    subset = benchmark_df.sample(n=min(subset_size, len(benchmark_df)), random_state=random.randint(0, 9999))
    solved, failed = [], []

    for _, row in subset.iterrows():
        cid = row['Conjecture ID']
        success, elapsed = _search_with_score(row, score_fn)
        status = "OK" if success else "--"
        print(f"  [{status}] Conjecture {cid} ({elapsed:.1f}s)")
        if success:
            solved.append(cid)
        else:
            failed.append(cid)

    return len(solved), {'solved': solved, 'failed': failed}
