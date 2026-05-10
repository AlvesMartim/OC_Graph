import random

import networkx as nx

from .utils import parse_subgroup


def make_connected(H):
    components = list(nx.connected_components(H))
    for i in range(len(components) - 1):
        u = random.choice(list(components[i]))
        v = random.choice(list(components[i + 1]))
        H.add_edge(u, v)
    return H


def make_tree(H):
    if H.number_of_nodes() == 0:
        return H
    if not nx.is_connected(H):
        H = make_connected(H)
    return nx.minimum_spanning_tree(H)


def remove_claws(H):
    """Détruit les griffes (K_{1,3}) en ajoutant des arêtes entre voisins indépendants."""
    for _ in range(200):
        claw_found = False
        for v in list(H.nodes()):
            neighbors = list(H.neighbors(v))
            if len(neighbors) < 3:
                continue
            for i in range(len(neighbors)):
                for j in range(i + 1, len(neighbors)):
                    if H.has_edge(neighbors[i], neighbors[j]):
                        continue
                    for k in range(j + 1, len(neighbors)):
                        a, b, c = neighbors[i], neighbors[j], neighbors[k]
                        if not H.has_edge(a, b) and not H.has_edge(b, c) and not H.has_edge(a, c):
                            H.add_edge(a, b)
                            claw_found = True
                            break
                    if claw_found:
                        break
                if claw_found:
                    break
            if claw_found:
                break
        if not claw_found:
            break
    return H


def repair_if_needed(H, graph_class):
    classes = parse_subgroup(graph_class)

    if 'tree' in classes:
        return make_tree(H)

    if 'connected' in classes and not nx.is_connected(H):
        H = make_connected(H)

    if 'claw_free' in classes:
        H = remove_claws(H)
        if 'connected' in classes and not nx.is_connected(H):
            H = make_connected(H)

    return H
