import random
import time

import networkx as nx

from .atlas import try_known_graphs
from .invariants import compute_invariants
from .mutations import random_mutation, targeted_mutate
from .repair import make_connected, repair_if_needed
from .utils import parse_subgroup, parse_fraction, parse_coefficients, eval_polynomial


# ----- Paramètres de diversification -----
TABU_MAX = 5000          # Taille max de la liste tabou (graph6 hashes)
KICK_THRESHOLD = 100     # Nb itérations avant de passer aux kick mutations
RESTART_THRESHOLD = 500  # Nb itérations avant un VRAI redémarrage complet
KICK_SIZE = 4            # Nb de mutations consécutives en kick
ATLAS_TIME_BUDGET = 5.0  # Temps max alloué à la passe atlas


def required_invariants(conjecture):
    needed = set()
    if conjecture.get('X'):
        needed.add(conjecture['X'])
    if conjecture.get('Y'):
        needed.add(conjecture['Y'])
    return needed


def violation_score(invariants, conjecture):
    try:
        X_val = float(invariants.get(conjecture['X'], 0))
        Y_val = float(invariants.get(conjecture['Y'], 0))

        coeffs = parse_coefficients(conjecture.get('Coefficients', ''))
        intercept_str = str(conjecture.get('Intercept', 0))

        f_X = None
        if coeffs:
            f_X = eval_polynomial(coeffs, intercept_str, X_val)

        if f_X is None:
            degree = parse_fraction(str(conjecture.get('Degree', 1)))
            intercept = parse_fraction(intercept_str) if intercept_str and intercept_str != 'nan' else 0.0
            f_X = degree * X_val + intercept

        sign = conjecture['Sign']
        if sign in ('<=', '<'):
            return Y_val - f_X
        elif sign in ('>=', '>'):
            return f_X - Y_val
        return -1

    except Exception as e:
        print(f"Erreur dans le calcul du score : {e}")
        return -float('inf')


def generate_initial_graphs(conjecture, num_graphs=10):
    classes = parse_subgroup(conjecture.get('Subgroup', "['connected']"))
    population = []
    for _ in range(num_graphs):
        n = random.randint(4, 15)
        try:
            if 'tree' in classes:
                G = nx.random_tree(n)
            elif 'claw_free' in classes:
                if random.random() < 0.3:
                    G = nx.complete_graph(random.randint(3, 10))
                else:
                    p = random.uniform(0.4, 0.8)
                    G = nx.gnp_random_graph(n, p)
                    G = repair_if_needed(G, conjecture.get('Subgroup'))
            else:
                p = random.uniform(0.2, 0.6)
                G = nx.gnp_random_graph(n, p)
                if not nx.is_connected(G):
                    G = make_connected(G)
            if G.number_of_nodes() > 0:
                population.append(G)
        except Exception:
            population.append(nx.path_graph(5))
    return population if population else [nx.path_graph(5)]


def select_candidate(scored_pop):
    k = min(3, len(scored_pop))
    tournament = random.sample(scored_pop, k)
    return max(tournament, key=lambda x: x[1])[0]


def mutate(G, conjecture=None):
    if conjecture is None:
        return random_mutation(G.copy())
    return targeted_mutate(G, conjecture)


def _graph_hash(G):
    """Hash basé sur graph6 ; retourne None si échec."""
    try:
        return nx.to_graph6_bytes(G).decode('ascii').strip()
    except Exception:
        return None


def _kick_mutate(G, conjecture, n_mutations):
    """Applique plusieurs mutations consécutives pour échapper aux plateaux."""
    H = G.copy()
    for _ in range(n_mutations):
        H = targeted_mutate(H, conjecture)
        if H.number_of_nodes() < 2:
            break
    return H


def counterexample_found(G, invariants, conjecture, score, elapsed):
    print("\n" + "=" * 50)
    print("Contre-exemple trouvé !")
    print(f"Conjecture: {conjecture['Conjecture']}")
    print(f"Graphe (graph6): {nx.to_graph6_bytes(G).decode('ascii').strip()}")
    print(f"Ordre: {invariants.get('order', 'N/A')}, Taille: {invariants.get('size', 'N/A')}")
    print(f"Invariants: {conjecture['X']}={invariants.get(conjecture['X'], 'N/A')}, "
          f"{conjecture['Y']}={invariants.get(conjecture['Y'], 'N/A')}")
    print(f"Score de violation: {score:.4f}")
    print(f"Temps de réfutation : {elapsed:.2f}s")
    print("=" * 50 + "\n")
    return G, elapsed


def run_heuristic(conjecture):
    """Retourne (graphe, durée) si contre-exemple trouvé, sinon (None, 60.0)."""
    start_time = time.time()
    graph_class = conjecture.get('Subgroup')
    needed = required_invariants(conjecture)

    # ---------- AXE 3 : passe atlas / graphes connus ----------
    atlas_result = try_known_graphs(conjecture, needed, violation_score,
                                    time_limit=ATLAS_TIME_BUDGET)
    if atlas_result:
        G, inv, s = atlas_result
        return counterexample_found(G, inv, conjecture, s, time.time() - start_time)

    # ---------- Recherche locale avec diversification ----------
    tabu = set()  # hashes graph6 des graphes déjà visités
    population = generate_initial_graphs(conjecture)

    scored_pop = []
    for G in population:
        inv = compute_invariants(G, needed=needed)
        s = violation_score(inv, conjecture)
        if s > 0:
            return counterexample_found(G, inv, conjecture, s, time.time() - start_time)
        scored_pop.append((G, s))
        h = _graph_hash(G)
        if h:
            tabu.add(h)

    scored_pop.sort(key=lambda x: x[1], reverse=True)
    scored_pop = scored_pop[:10]
    best_score = scored_pop[0][1]
    stagnation = 0

    while time.time() - start_time < 60:
        G = select_candidate(scored_pop)

        # Kick mutations : plusieurs mutations consécutives si stagnation
        n_mutations = KICK_SIZE if stagnation > KICK_THRESHOLD else 1
        H = _kick_mutate(G, conjecture, n_mutations)

        if graph_class:
            H = repair_if_needed(H, graph_class)

        if H.number_of_nodes() < 2:
            stagnation += 1
            continue

        # Tabou : éviter de revisiter
        h = _graph_hash(H)
        if h and h in tabu:
            stagnation += 1
            continue
        if h and len(tabu) < TABU_MAX:
            tabu.add(h)

        inv = compute_invariants(H, needed=needed)
        score = violation_score(inv, conjecture)

        if score > 0:
            return counterexample_found(H, inv, conjecture, score, time.time() - start_time)

        if score > best_score:
            best_score = score
            stagnation = 0
            scored_pop.append((H, score))
            scored_pop.sort(key=lambda x: x[1], reverse=True)
            scored_pop = scored_pop[:10]
        else:
            stagnation += 1

        # Vrai redémarrage : remplacer TOUTE la population (pas juste 5/10)
        if stagnation > RESTART_THRESHOLD:
            new_pop = generate_initial_graphs(conjecture)
            scored_pop = []
            for G_new in new_pop:
                inv_new = compute_invariants(G_new, needed=needed)
                s_new = violation_score(inv_new, conjecture)
                if s_new > 0:
                    return counterexample_found(G_new, inv_new, conjecture, s_new,
                                                time.time() - start_time)
                scored_pop.append((G_new, s_new))
                h_new = _graph_hash(G_new)
                if h_new and len(tabu) < TABU_MAX:
                    tabu.add(h_new)
            scored_pop.sort(key=lambda x: x[1], reverse=True)
            scored_pop = scored_pop[:10]
            best_score = scored_pop[0][1]  # plafond local réinitialisé
            stagnation = 0

    return None, 60.0
