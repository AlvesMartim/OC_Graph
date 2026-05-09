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
