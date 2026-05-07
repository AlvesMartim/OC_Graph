import random
import time

import networkx as nx

from .invariants import compute_invariants
from .repair import make_connected, remove_claws, repair_if_needed
from .utils import parse_subgroup, parse_fraction, parse_coefficients, eval_polynomial


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
    """Sélection par tournoi (k=3)."""
    k = min(3, len(scored_pop))
    tournament = random.sample(scored_pop, k)
    return max(tournament, key=lambda x: x[1])[0]


def mutate(G):
    H = G.copy()
    mutations = ['add_edge', 'remove_edge', 'remove_node']
    if H.number_of_nodes() < 30:
        mutations.append('add_node')
    mutation_type = random.choice(mutations)

    if mutation_type == 'add_edge':
        nodes = list(H.nodes())
        if len(nodes) > 1:
            u, v = random.sample(nodes, 2)
            if not H.has_edge(u, v):
                H.add_edge(u, v)
    elif mutation_type == 'remove_edge':
        edges = list(H.edges())
        if edges:
            H.remove_edge(*random.choice(edges))
    elif mutation_type == 'add_node':
        new_node = max(H.nodes(), default=-1) + 1
        H.add_node(new_node)
        if H.number_of_nodes() > 1:
            target = random.choice([n for n in H.nodes() if n != new_node])
            H.add_edge(new_node, target)
    elif mutation_type == 'remove_node':
        nodes = list(H.nodes())
        if nodes:
            H.remove_node(random.choice(nodes))
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

    population = generate_initial_graphs(conjecture)

    scored_pop = []
    for G in population:
        inv = compute_invariants(G)
        s = violation_score(inv, conjecture)
        if s > 0:
            return counterexample_found(G, inv, conjecture, s, time.time() - start_time)
        scored_pop.append((G, s))

    scored_pop.sort(key=lambda x: x[1], reverse=True)
    scored_pop = scored_pop[:10]

    best_score = scored_pop[0][1]
    stagnation = 0

    while time.time() - start_time < 60:
        G = select_candidate(scored_pop)
        H = mutate(G)

        if graph_class:
            H = repair_if_needed(H, graph_class)

        if H.number_of_nodes() < 2:
            continue

        inv = compute_invariants(H)
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

        if stagnation > 300:
            for G_new in generate_initial_graphs(conjecture, num_graphs=5):
                inv_new = compute_invariants(G_new)
                s_new = violation_score(inv_new, conjecture)
                if s_new > 0:
                    return counterexample_found(G_new, inv_new, conjecture, s_new, time.time() - start_time)
                scored_pop.append((G_new, s_new))
            scored_pop.sort(key=lambda x: x[1], reverse=True)
            scored_pop = scored_pop[:10]
            stagnation = 0

    return None, 60.0
