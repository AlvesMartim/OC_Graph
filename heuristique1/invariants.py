import networkx as nx
import numpy as np


# -----------------------------------------------------------------------------
# Tier 1 : invariants toujours calculés (très peu coûteux, utiles pour mutations
# et réparations). Ils dérivent tous des degrés.
# -----------------------------------------------------------------------------
TIER_1 = {
    'order', 'size',
    'minimum_degree', 'maximum_degree', 'average_degree', 'density',
    'first_zagreb_index', 'second_zagreb_index', 'randic_index', 'harmonic_index',
}

# Dépendances entre invariants (pour expansion automatique du `needed`)
DEPS = {
    'vertex_cover_number': {'independence_number', 'order'},
}


def _expand(needed):
    """Étend l'ensemble `needed` avec les dépendances transitives + tier 1."""
    expanded = set(needed) | TIER_1
    while True:
        new = set()
        for inv in expanded:
            new |= DEPS.get(inv, set())
        if new <= expanded:
            break
        expanded |= new
    return expanded


def _greedy_total_dominating_set(G):
    nodes = set(G.nodes())
    covered = set()
    S = set()
    while covered != nodes:
        candidates = [(v, len(set(G.neighbors(v)) - covered)) for v in nodes - S]
        if not candidates:
            break
        best, gain = max(candidates, key=lambda x: x[1])
        if gain == 0:
            break
        S.add(best)
        covered.update(G.neighbors(best))
    return S


def compute_invariants(G, needed=None):
    """
    Calcule les invariants. Si `needed` est fourni (set de noms d'invariants),
    seuls ceux-là (+ tier 1 + dépendances transitives) sont calculés. Si None,
    tous les invariants sont calculés (rétrocompatibilité).
    """
    if needed is None:
        compute_all = True
    else:
        compute_all = False
        needed = _expand(needed)

    def need(name):
        return compute_all or name in needed

    invariants = {}
    try:
        G_clean = G.copy()
        G_clean.remove_edges_from(nx.selfloop_edges(G_clean))

        n = G_clean.number_of_nodes()
        m = G_clean.number_of_edges()
        invariants['order'] = n
        invariants['size'] = m

        if n < 2:
            return invariants

        # ------ Tier 1 : degrés et indices topologiques (toujours calculés) ------
        degrees = dict(G_clean.degree())
        deg_vals = list(degrees.values())
        invariants['minimum_degree'] = min(deg_vals)
        invariants['maximum_degree'] = max(deg_vals)
        invariants['average_degree'] = sum(deg_vals) / n
        invariants['density'] = 2 * m / (n * (n - 1))
        invariants['first_zagreb_index'] = sum(d ** 2 for d in deg_vals)
        invariants['second_zagreb_index'] = sum(degrees[u] * degrees[v] for u, v in G_clean.edges())
        invariants['randic_index'] = sum(
            1.0 / (degrees[u] * degrees[v]) ** 0.5
            for u, v in G_clean.edges()
            if degrees[u] > 0 and degrees[v] > 0
        )
        invariants['harmonic_index'] = sum(
            2.0 / (degrees[u] + degrees[v])
            for u, v in G_clean.edges()
            if degrees[u] + degrees[v] > 0
        )

        connected = None  # lazy

        def is_connected():
            nonlocal connected
            if connected is None:
                connected = nx.is_connected(G_clean)
            return connected

        # ------ Distances ------
        if need('diameter') or need('radius'):
            if is_connected():
                invariants['diameter'] = nx.diameter(G_clean)
                invariants['radius'] = nx.radius(G_clean)
            else:
                invariants['diameter'] = float('inf')
                invariants['radius'] = float('inf')

        # ------ Spectral ------
        if need('largest_eigenvalue'):
            A = nx.to_numpy_array(G_clean)
            invariants['largest_eigenvalue'] = float(np.max(np.linalg.eigvalsh(A)))

        if need('second_smallest_laplace_eigenvalue'):
            L = nx.laplacian_matrix(G_clean).toarray().astype(float)
            eig_L = sorted(np.linalg.eigvalsh(L))
            invariants['second_smallest_laplace_eigenvalue'] = float(eig_L[1]) if len(eig_L) > 1 else 0.0

        # ------ Distance matrix (proximity, remoteness, distance eigenvalues) ------
        if need('largest_distance_eigenvalue') or need('proximity') or need('remoteness'):
            if is_connected() and n <= 60:
                dist = nx.floyd_warshall_numpy(G_clean)
                if need('largest_distance_eigenvalue'):
                    invariants['largest_distance_eigenvalue'] = float(np.max(np.linalg.eigvalsh(dist)))
                if need('proximity') or need('remoteness'):
                    avg_dists = dist.mean(axis=1)
                    invariants['proximity'] = float(np.min(avg_dists))
                    invariants['remoteness'] = float(np.max(avg_dists))
            else:
                if need('largest_distance_eigenvalue'):
                    invariants['largest_distance_eigenvalue'] = float('inf')
                if need('proximity'):
                    invariants['proximity'] = float('inf')
                if need('remoteness'):
                    invariants['remoteness'] = float('inf')

        # ------ Combinatoire ------
        if need('triangle_number'):
            invariants['triangle_number'] = sum(nx.triangles(G_clean).values()) // 3

        if need('clique_number'):
            cliques = list(nx.find_cliques(G_clean))
            invariants['clique_number'] = len(max(cliques, key=len)) if cliques else 0

        if need('domination_number'):
            invariants['domination_number'] = len(nx.dominating_set(G_clean))

        if need('matching_number'):
            invariants['matching_number'] = len(nx.max_weight_matching(G_clean, maxcardinality=True))

        if need('independence_number') or need('vertex_cover_number') or need('independent_domination_number'):
            best_indep = 0
            best_idom = float('inf')
            for _ in range(8):
                indep = nx.maximal_independent_set(G_clean)
                best_indep = max(best_indep, len(indep))
                best_idom = min(best_idom, len(indep))
            invariants['independence_number'] = best_indep
            invariants['vertex_cover_number'] = n - best_indep
            invariants['independent_domination_number'] = best_idom if best_idom != float('inf') else 0

        if need('total_domination_number'):
            if is_connected() and m > 0:
                invariants['total_domination_number'] = len(_greedy_total_dominating_set(G_clean))
            else:
                invariants['total_domination_number'] = 0

        if need('node_connectivity') or need('edge_connectivity'):
            if is_connected():
                invariants['node_connectivity'] = nx.node_connectivity(G_clean)
                invariants['edge_connectivity'] = nx.edge_connectivity(G_clean)
            else:
                invariants['node_connectivity'] = 0
                invariants['edge_connectivity'] = 0

    except Exception as e:
        print(f"Erreur lors du calcul des invariants : {e}")
    return invariants
