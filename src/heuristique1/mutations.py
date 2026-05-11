import random

import networkx as nx


# -----------------------------------------------------------------------------
# Mutations de base
# -----------------------------------------------------------------------------

def _add_random_edge(H):
    nodes = list(H.nodes())
    if len(nodes) < 2:
        return H
    u, v = random.sample(nodes, 2)
    if not H.has_edge(u, v):
        H.add_edge(u, v)
    return H


def _remove_random_edge(H):
    edges = list(H.edges())
    if edges:
        H.remove_edge(*random.choice(edges))
    return H


def _add_node(H):
    new_node = max(H.nodes(), default=-1) + 1
    H.add_node(new_node)
    if H.number_of_nodes() > 1:
        target = random.choice([n for n in H.nodes() if n != new_node])
        H.add_edge(new_node, target)
    return H


def _remove_node(H):
    nodes = list(H.nodes())
    if nodes:
        H.remove_node(random.choice(nodes))
    return H


def random_mutation(H):
    """Mutation aléatoire pure (ancien comportement)."""
    mutations = ['add_edge', 'remove_edge', 'remove_node']
    if H.number_of_nodes() < 30:
        mutations.append('add_node')
    mt = random.choice(mutations)
    if mt == 'add_edge':
        return _add_random_edge(H)
    elif mt == 'remove_edge':
        return _remove_random_edge(H)
    elif mt == 'add_node':
        return _add_node(H)
    elif mt == 'remove_node':
        return _remove_node(H)
    return H


# -----------------------------------------------------------------------------
# Mutations ciblées : (increase_fn, decrease_fn) par invariant cible
# -----------------------------------------------------------------------------

def _increase_triangle(H):
    """Crée un triangle : arête entre deux voisins non-connectés."""
    nodes = list(H.nodes())
    random.shuffle(nodes)
    for v in nodes:
        neighbors = list(H.neighbors(v))
        if len(neighbors) < 2:
            continue
        random.shuffle(neighbors)
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                if not H.has_edge(neighbors[i], neighbors[j]):
                    H.add_edge(neighbors[i], neighbors[j])
                    return H
    return _add_random_edge(H)


def _decrease_triangle(H):
    """Détruit un triangle : retire une arête appartenant à un triangle."""
    edges = list(H.edges())
    random.shuffle(edges)
    for u, v in edges:
        if set(H.neighbors(u)) & set(H.neighbors(v)):
            H.remove_edge(u, v)
            return H
    return _remove_random_edge(H)


def _increase_max_degree(H):
    """Connecte le sommet de degré max à un sommet non-voisin."""
    if H.number_of_nodes() < 2:
        return _add_node(H)
    degrees = dict(H.degree())
    v_max = max(degrees, key=degrees.get)
    non_neighbors = [u for u in H.nodes() if u != v_max and not H.has_edge(v_max, u)]
    if non_neighbors:
        H.add_edge(v_max, random.choice(non_neighbors))
        return H
    if H.number_of_nodes() < 30:
        new_node = max(H.nodes()) + 1
        H.add_node(new_node)
        H.add_edge(v_max, new_node)
    return H


def _decrease_max_degree(H):
    """Retire une arête incidente au sommet de degré max."""
    if H.number_of_edges() == 0:
        return H
    degrees = dict(H.degree())
    v_max = max(degrees, key=degrees.get)
    neighbors = list(H.neighbors(v_max))
    if neighbors:
        H.remove_edge(v_max, random.choice(neighbors))
    return H


def _increase_min_degree(H):
    """Connecte le sommet de degré min à un sommet non-voisin."""
    if H.number_of_nodes() < 2:
        return _add_node(H)
    degrees = dict(H.degree())
    v_min = min(degrees, key=degrees.get)
    non_neighbors = [u for u in H.nodes() if u != v_min and not H.has_edge(v_min, u)]
    if non_neighbors:
        H.add_edge(v_min, random.choice(non_neighbors))
    return H


def _decrease_min_degree(H):
    """Retire une arête incidente au sommet de degré min, ou ajoute un sommet isolé."""
    if H.number_of_nodes() < 30 and random.random() < 0.5:
        new_node = max(H.nodes(), default=-1) + 1
        H.add_node(new_node)
        return H
    degrees = dict(H.degree())
    candidates = [v for v in H.nodes() if degrees[v] > 0]
    if candidates:
        v_min = min(candidates, key=lambda x: degrees[x])
        neighbors = list(H.neighbors(v_min))
        if neighbors:
            H.remove_edge(v_min, random.choice(neighbors))
    return H


def _increase_clique(H):
    """Étend la plus grande clique en ajoutant une arête entre la clique et l'extérieur."""
    try:
        cliques = list(nx.find_cliques(H))
        if not cliques:
            return _add_random_edge(H)
        max_clique = list(max(cliques, key=len))
        outside = [v for v in H.nodes() if v not in max_clique]
        random.shuffle(outside)
        for v in outside:
            missing = [u for u in max_clique if not H.has_edge(v, u)]
            if missing:
                H.add_edge(v, random.choice(missing))
                return H
    except Exception:
        pass
    return _add_random_edge(H)


def _decrease_clique(H):
    """Casse la plus grande clique en retirant une arête interne."""
    try:
        cliques = list(nx.find_cliques(H))
        if not cliques:
            return _remove_random_edge(H)
        max_clique = list(max(cliques, key=len))
        if len(max_clique) >= 2:
            u, v = random.sample(max_clique, 2)
            if H.has_edge(u, v):
                H.remove_edge(u, v)
                return H
    except Exception:
        pass
    return _remove_random_edge(H)


def _increase_diameter(H):
    """Augmente le diamètre : ajoute un sommet relié à une feuille."""
    if H.number_of_nodes() == 0 or H.number_of_nodes() >= 30:
        return _add_random_edge(H)
    leaves = [v for v in H.nodes() if H.degree(v) == 1]
    if not leaves:
        leaves = [v for v in H.nodes() if H.degree(v) <= 2]
    if leaves:
        leaf = random.choice(leaves)
        new_node = max(H.nodes()) + 1
        H.add_node(new_node)
        H.add_edge(new_node, leaf)
    else:
        _add_node(H)
    return H


def _decrease_diameter(H):
    """Diminue le diamètre : ajoute un raccourci entre deux sommets distants."""
    if H.number_of_nodes() < 4 or not nx.is_connected(H):
        return _add_random_edge(H)
    nodes = list(H.nodes())
    best_pair = None
    best_dist = 0
    for _ in range(20):
        u, v = random.sample(nodes, 2)
        if not H.has_edge(u, v):
            try:
                d = nx.shortest_path_length(H, u, v)
                if d > best_dist:
                    best_dist = d
                    best_pair = (u, v)
            except nx.NetworkXNoPath:
                pass
    if best_pair:
        H.add_edge(*best_pair)
    else:
        _add_random_edge(H)
    return H


def _increase_matching(H):
    """Ajoute une arête entre deux sommets non-couverts par le matching."""
    try:
        matching = nx.max_weight_matching(H, maxcardinality=True)
        matched = set()
        for u, v in matching:
            matched.update((u, v))
        unmatched = [v for v in H.nodes() if v not in matched]
        if len(unmatched) >= 2:
            u, v = random.sample(unmatched, 2)
            if not H.has_edge(u, v):
                H.add_edge(u, v)
                return H
    except Exception:
        pass
    return _add_random_edge(H)


def _decrease_matching(H):
    """Retire une arête du matching maximum."""
    try:
        matching = nx.max_weight_matching(H, maxcardinality=True)
        if matching:
            u, v = random.choice(list(matching))
            H.remove_edge(u, v)
            return H
    except Exception:
        pass
    return _remove_random_edge(H)


def _decrease_proximity(H):
    """Diminue la proximity (min des dist. moy.) : créer un hub central.
    Connecte le sommet de plus petite distance moyenne à des non-voisins
    pour le rapprocher de tous, ce qui fait chuter min(avg_dist).
    """
    if H.number_of_nodes() < 3 or not nx.is_connected(H):
        return _add_random_edge(H)
    try:
        dist = dict(nx.all_pairs_shortest_path_length(H))
        n = H.number_of_nodes()
        avg = {v: sum(dist[v].values()) / (n - 1) for v in H.nodes()}
        v_hub = min(avg, key=avg.get)
        non_neighbors = [u for u in H.nodes() if u != v_hub and not H.has_edge(v_hub, u)]
        if non_neighbors:
            H.add_edge(v_hub, random.choice(non_neighbors))
            return H
    except Exception:
        pass
    return _add_random_edge(H)


def _increase_proximity(H):
    """Augmente la proximity : étaler le graphe (chemins longs, sommets pendants éloignés).
    Retire une arête au "centre" et/ou ajoute un sommet pendant à un sommet excentrique.
    """
    if H.number_of_nodes() < 3:
        return _add_node(H)
    if H.number_of_nodes() < 30 and random.random() < 0.5:
        try:
            if nx.is_connected(H):
                ecc = nx.eccentricity(H)
                v_far = max(ecc, key=ecc.get)
                new_node = max(H.nodes()) + 1
                H.add_node(new_node)
                H.add_edge(new_node, v_far)
                return H
        except Exception:
            pass
    if H.number_of_edges() > H.number_of_nodes():
        try:
            dist = dict(nx.all_pairs_shortest_path_length(H))
            n = H.number_of_nodes()
            avg = {v: sum(dist[v].values()) / (n - 1) for v in H.nodes()}
            v_center = min(avg, key=avg.get)
            neighbors = list(H.neighbors(v_center))
            if neighbors:
                u = random.choice(neighbors)
                H.remove_edge(v_center, u)
                if nx.is_connected(H):
                    return H
                H.add_edge(v_center, u)  # rollback
        except Exception:
            pass
    return _remove_random_edge(H)


def _increase_independence(H):
    """Augmente l'indépendance : retirer des arêtes."""
    return _remove_random_edge(H)


def _decrease_independence(H):
    """Diminue l'indépendance : densifier."""
    return _add_random_edge(H)


# Mappage invariant -> (increase, decrease)
TARGETED = {
    'triangle_number':       (_increase_triangle,    _decrease_triangle),
    'maximum_degree':        (_increase_max_degree,  _decrease_max_degree),
    'minimum_degree':        (_increase_min_degree,  _decrease_min_degree),
    'first_zagreb_index':    (_increase_max_degree,  _decrease_max_degree),
    'second_zagreb_index':   (_increase_max_degree,  _decrease_max_degree),
    'largest_eigenvalue':    (_increase_max_degree,  _decrease_max_degree),
    'average_degree':        (_add_random_edge,      _remove_random_edge),
    'size':                  (_add_random_edge,      _remove_random_edge),
    'density':               (_add_random_edge,      _remove_random_edge),
    'clique_number':         (_increase_clique,      _decrease_clique),
    'diameter':              (_increase_diameter,    _decrease_diameter),
    'radius':                (_increase_diameter,    _decrease_diameter),
    'remoteness':            (_increase_diameter,    _decrease_diameter),
    'proximity':             (_increase_proximity,   _decrease_proximity),
    'matching_number':       (_increase_matching,    _decrease_matching),
    'independence_number':   (_increase_independence, _decrease_independence),
    'vertex_cover_number':   (_decrease_independence, _increase_independence),
}


def targeted_mutate(G, conjecture, p_targeted=0.7):
    """
    Mutation orientée par la conjecture :
    - Avec probabilité p_targeted, mutation ciblée selon Y et le sens de l'inégalité
    - Sinon, mutation aléatoire (préserve la diversité)
    """
    H = G.copy()

    if random.random() > p_targeted:
        return random_mutation(H)

    Y = conjecture.get('Y')
    sign = conjecture.get('Sign', '<=')
    # Pour Y <= f(X), violation = Y - f(X) maximisée → augmenter Y
    # Pour Y >= f(X), violation = f(X) - Y maximisée → diminuer Y
    direction = 'increase' if sign in ('<=', '<') else 'decrease'

    if Y in TARGETED:
        increase_fn, decrease_fn = TARGETED[Y]
        fn = increase_fn if direction == 'increase' else decrease_fn
        try:
            return fn(H)
        except Exception:
            return random_mutation(H)

    return random_mutation(H)
