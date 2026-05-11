# test de ptits graphes connus : 1252 graphes à <= 7 sommets, puis arbres à 8..12 sommets
import time
import networkx as nx

from .invariants import compute_invariants
from .utils import parse_subgroup


def is_claw_free(G):
    """Vrai si G ne contient pas de K_{1,3} induit."""
    for v in G.nodes():
        neighbors = list(G.neighbors(v))
        if len(neighbors) < 3:
            continue
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                if G.has_edge(neighbors[i], neighbors[j]):
                    continue
                for k in range(j + 1, len(neighbors)):
                    if (not G.has_edge(neighbors[i], neighbors[k])
                            and not G.has_edge(neighbors[j], neighbors[k])):
                        return False
    return True


def _matches_class(G, classes):
    if not classes:
        return True
    if 'connected' in classes and not nx.is_connected(G):
        return False
    if 'tree' in classes and not nx.is_tree(G):
        return False
    if 'claw_free' in classes and not is_claw_free(G):
        return False
    return True


def _parametric_families(classes):
    """Familles paramétriques structurées (n = 8..25) pour étendre l'atlas."""
    sizes = list(range(8, 26))
    for n in sizes:
        yield nx.path_graph(n)
        yield nx.cycle_graph(n)

        if 'claw_free' not in classes:
            yield nx.star_graph(n - 1)

        if n <= 12:
            yield nx.complete_graph(n)

        if 'tree' not in classes and n >= 4:
            yield nx.wheel_graph(n)

        # Caterpillar : path + feuilles
        if n >= 6 and 'connected' in classes or 'tree' in classes:
            for ext in (1, 2):
                spine = max(3, n - ext * (n // 2))
                G = nx.path_graph(spine)
                next_id = spine
                for v in range(1, spine - 1):
                    for _ in range(ext):
                        if next_id >= n:
                            break
                        G.add_node(next_id)
                        G.add_edge(v, next_id)
                        next_id += 1
                yield G

        # Double-star
        if n >= 5:
            for split in (n // 3, n // 2):
                a = split
                b = n - a - 2
                if a >= 1 and b >= 1:
                    G = nx.Graph()
                    G.add_edge(0, 1)
                    for i in range(a):
                        G.add_edge(0, 2 + i)
                    for i in range(b):
                        G.add_edge(1, 2 + a + i)
                    yield G

        # Bipartis complets
        if 'claw_free' not in classes and 'tree' not in classes and n >= 4:
            for a in (2, 3, n // 2):
                b = n - a
                if 1 <= a <= b:
                    yield nx.complete_bipartite_graph(a, b)

        # Complément d'un chemin (souvent claw_free pour n grand)
        if n <= 15 and 'tree' not in classes:
            yield nx.complement(nx.path_graph(n))

        # Petersen
        if n == 10 and 'tree' not in classes:
            yield nx.petersen_graph()

    # Trees additionnels par construction (au-delà de nonisomorphic_trees 12)
    if 'tree' in classes:
        for n in range(13, 26):
            # Path
            yield nx.path_graph(n)
            # Broom : path attaché à étoile
            for spine in (3, n // 3, n // 2):
                if 2 <= spine < n:
                    leaves = n - spine
                    G = nx.path_graph(spine)
                    for i in range(leaves):
                        G.add_edge(spine - 1, spine + i)
                    yield G


def iter_known_graphs(classes):
    """Itère sur les graphes candidats respectant la classe."""
    for G in nx.graph_atlas_g():
        if G.number_of_nodes() < 2:
            continue
        if _matches_class(G, classes):
            yield G

    if 'tree' in classes:
        for n in range(8, 13):
            try:
                for T in nx.nonisomorphic_trees(n):
                    yield T
            except Exception:
                break

    for G in _parametric_families(classes):
        if G is None or G.number_of_nodes() < 2:
            continue
        if _matches_class(G, classes):
            yield G


def try_known_graphs(conjecture, needed, score_fn, time_limit=5.0):
    """
    Retourne
            (G, invariants, score) ou None.

    """
    classes = parse_subgroup(conjecture.get('Subgroup', ''))
    start = time.time()

    for G in iter_known_graphs(classes):
        if time.time() - start > time_limit:
            break
        inv = compute_invariants(G, needed=needed)
        s = score_fn(inv, conjecture)
        if s > 0:
            return G, inv, s
    return None
