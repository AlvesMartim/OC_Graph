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


def _random_tree(n):
    """Compatible NetworkX 2.x / 3.x."""
    if hasattr(nx, 'random_labeled_tree'):
        return nx.random_labeled_tree(n)
    return nx.random_tree(n)


def _specialized_seeds(conjecture):
    """Graphes structurés adaptés à l'invariant Y et au sens de l'inégalité.
    Retourne une liste de seeds (peut être vide)."""
    Y = conjecture.get('Y')
    X = conjecture.get('X')
    sign = conjecture.get('Sign', '<=')
    classes = parse_subgroup(conjecture.get('Subgroup', ''))
    seeds = []

    # Direction : pour Y <= f(X) on veut Y grand ; pour Y >= f(X) on veut Y petit.
    need_y_small = sign in ('>=', '>')
    proximity_involved = (Y == 'proximity') or (X == 'proximity')
    remoteness_involved = (Y == 'remoteness') or (X == 'remoteness')

    # K_n + bras : claw_free, remoteness basse (min_T élevé car nœuds lointains)
    # Efficace pour conjonctures density/remoteness et radius/remoteness
    if remoteness_involved and need_y_small:
        for n_clique in (5, 8, 10, 14):
            for arm_len in (5, 8, 10, 14):
                if n_clique + arm_len > 32:
                    continue
                G = nx.complete_graph(n_clique)
                for i in range(arm_len):
                    G.add_edge(n_clique - 1 + i, n_clique + i)
                seeds.append(G)

    if proximity_involved:
        # proximity = (n-1)/max_T. PETITE ↔ max_T grand ↔ graphe étalé.
        #                          GRANDE ↔ max_T petit ↔ graphe compact.
        # On inclut les deux types : la direction utile dépend du signe du coefficient.

        # Compacts : haute proximity
        for n in (6, 10, 14, 20):
            seeds.append(nx.complete_graph(min(n, 12)))
            seeds.append(nx.complete_bipartite_graph(max(2, n // 3), n - max(2, n // 3)))

        # Étalés : basse proximity (chemins, cycles)
        for n in (6, 10, 15, 20, 25):
            seeds.append(nx.path_graph(n))
            seeds.append(nx.cycle_graph(n))

        # Double-stars TRÈS DÉSÉQUILIBRÉES : a feuilles d'un côté, 1 de l'autre.
        # Donne total_dom=2 et proximity ≈ 1/3 pour a grand.
        for n_total in (8, 11, 15, 20, 25):
            for b in (1, 2):
                a = n_total - 2 - b
                if a >= 2:
                    G = nx.Graph()
                    G.add_edge(0, 1)
                    for i in range(a):
                        G.add_edge(0, 2 + i)
                    for i in range(b):
                        G.add_edge(1, 2 + a + i)
                    seeds.append(G)

        # Brooms (chemin + étoile à un bout) : aussi total_dom petit et étalé
        for n_total in (8, 12, 18):
            for spine in (3, 4, 5):
                if spine < n_total:
                    G = nx.path_graph(spine)
                    for i in range(n_total - spine):
                        G.add_edge(spine - 1, spine + i)
                    seeds.append(G)

    # Filtre selon la classe
    valid = []
    for G in seeds:
        if 'tree' in classes and not nx.is_tree(G):
            continue
        if 'connected' in classes and not nx.is_connected(G):
            continue
        if 'claw_free' in classes:
            from .atlas import is_claw_free
            if not is_claw_free(G):
                continue
        valid.append(G)
    return valid


def generate_initial_graphs(conjecture, num_graphs=10):
    classes = parse_subgroup(conjecture.get('Subgroup', "['connected']"))
    population = list(_specialized_seeds(conjecture))[:num_graphs]

    while len(population) < num_graphs:
        n = random.randint(4, 15)
        try:
            if 'tree' in classes:
                G = _random_tree(n)
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


def _describe_mutation(G_before, G_after):
    """Décrit en texte les changements entre deux graphes."""
    nodes_before = set(G_before.nodes())
    nodes_after = set(G_after.nodes())
    edges_before = set(frozenset(e) for e in G_before.edges())
    edges_after = set(frozenset(e) for e in G_after.edges())

    parts = []
    for n in nodes_after - nodes_before:
        parts.append(f"sommet {n} ajouté")
    for n in nodes_before - nodes_after:
        parts.append(f"sommet {n} supprimé")
    for e in edges_after - edges_before:
        u, v = tuple(e)
        parts.append(f"arête ({u},{v}) ajoutée")
    for e in edges_before - edges_after:
        u, v = tuple(e)
        parts.append(f"arête ({u},{v}) supprimée")
    return ", ".join(parts) if parts else "aucun changement"


def _kick_mutate(G, conjecture, n_mutations):
    """Applique plusieurs mutations consécutives ; retourne (graphe, description)."""
    H = G.copy()
    steps = []
    for _ in range(n_mutations):
        H_prev = H.copy()
        H = targeted_mutate(H, conjecture)
        steps.append(_describe_mutation(H_prev, H))
        if H.number_of_nodes() < 2:
            break
    return H, " → ".join(steps)


def counterexample_found(G, invariants, conjecture, score, elapsed, history=None):
    g6 = nx.to_graph6_bytes(G).decode('ascii').strip()
    print("\n" + "=" * 50)
    print("Contre-exemple trouvé !")
    print(f"Conjecture: {conjecture['Conjecture']}")
    print(f"Graphe (graph6): {g6}")
    print(f"Ordre: {invariants.get('order', 'N/A')}, Taille: {invariants.get('size', 'N/A')}")
    print(f"Invariants: {conjecture['X']}={invariants.get(conjecture['X'], 'N/A')}, "
          f"{conjecture['Y']}={invariants.get(conjecture['Y'], 'N/A')}")
    print(f"Score de violation: {score:.4f}")
    print(f"Temps de réfutation : {elapsed:.2f}s")
    if history:
        print(f"\nChemin ({len(history)} étape(s)) :")
        MAX_STEPS = 10
        display = history if len(history) <= MAX_STEPS else history[:5] + ["..."] + history[-3:]
        for i, step in enumerate(display, start=1):
            prefix = f"  {i}." if step != "..." else "  ..."
            print(f"{prefix} {step}")
    print("=" * 50 + "\n")

    info = {
        "graph6": g6,
        "order": invariants.get('order'),
        "size": invariants.get('size'),
        conjecture['X']: invariants.get(conjecture['X']),
        conjecture['Y']: invariants.get(conjecture['Y']),
        "violation_score": round(float(score), 6),
        "refutation_time_s": round(elapsed, 3),
        "mutation_path": history or [],
    }
    return G, elapsed, info


def run_heuristic(conjecture):
    """Retourne (graphe, durée, info) si contre-exemple trouvé, sinon (None, 120.0, None)."""
    start_time = time.time()
    graph_class = conjecture.get('Subgroup')
    needed = required_invariants(conjecture)

    # ---------- AXE 3 : passe atlas / graphes connus ----------
    atlas_result = try_known_graphs(conjecture, needed, violation_score,
                                    time_limit=ATLAS_TIME_BUDGET)
    if atlas_result:
        G, inv, s = atlas_result
        g6 = _graph_hash(G) or "?"
        G_out, elapsed, info = counterexample_found(G, inv, conjecture, s, time.time() - start_time,
                                                    history=[f"Graphe de l'atlas ({g6})"])
        return G_out, elapsed, info

    # ---------- Recherche locale avec diversification ----------
    tabu = set()
    population = generate_initial_graphs(conjecture)

    # scored_pop : liste de (G, score, historique_mutations)
    scored_pop = []
    for G in population:
        inv = compute_invariants(G, needed=needed)
        s = violation_score(inv, conjecture)
        g6 = _graph_hash(G) or "?"
        history = [f"Graphe initial ({g6}, {G.number_of_nodes()} sommets, {G.number_of_edges()} arêtes)"]
        if s > 0:
            G_out, elapsed, info = counterexample_found(G, inv, conjecture, s, time.time() - start_time, history)
            return G_out, elapsed, info
        scored_pop.append((G, s, history))
        if g6 != "?":
            tabu.add(g6)

    scored_pop.sort(key=lambda x: x[1], reverse=True)
    scored_pop = scored_pop[:10]
    best_score = scored_pop[0][1]
    stagnation = 0

    while time.time() - start_time < 60:
        G, _, parent_history = max(
            random.sample(scored_pop, min(3, len(scored_pop))),
            key=lambda x: x[1]
        )

        # Kick mutations : plusieurs mutations consécutives si stagnation
        n_mutations = KICK_SIZE if stagnation > KICK_THRESHOLD else 1
        H, mut_desc = _kick_mutate(G, conjecture, n_mutations)

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
        new_history = parent_history + [mut_desc]

        if score > 0:
            G_out, elapsed, info = counterexample_found(H, inv, conjecture, score,
                                                        time.time() - start_time, new_history)
            return G_out, elapsed, info

        if score > best_score:
            best_score = score
            stagnation = 0
            scored_pop.append((H, score, new_history))
            scored_pop.sort(key=lambda x: x[1], reverse=True)
            scored_pop = scored_pop[:10]
        else:
            stagnation += 1

        # Vrai redémarrage : remplacer TOUTE la population
        if stagnation > RESTART_THRESHOLD:
            new_pop = generate_initial_graphs(conjecture)
            scored_pop = []
            for G_new in new_pop:
                inv_new = compute_invariants(G_new, needed=needed)
                s_new = violation_score(inv_new, conjecture)
                g6_new = _graph_hash(G_new) or "?"
                hist_new = [f"Redémarrage — graphe initial ({g6_new}, "
                            f"{G_new.number_of_nodes()} sommets, {G_new.number_of_edges()} arêtes)"]
                if s_new > 0:
                    G_out, elapsed, info = counterexample_found(G_new, inv_new, conjecture, s_new,
                                                                time.time() - start_time, hist_new)
                    return G_out, elapsed, info
                scored_pop.append((G_new, s_new, hist_new))
                if g6_new != "?" and len(tabu) < TABU_MAX:
                    tabu.add(g6_new)
            scored_pop.sort(key=lambda x: x[1], reverse=True)
            scored_pop = scored_pop[:10]
            best_score = scored_pop[0][1]
            stagnation = 0

    return None, 120.0, None
