import networkx as nx
import numpy as np


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


def compute_invariants(G):
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

        connected = nx.is_connected(G_clean)
        if connected:
            invariants['diameter'] = nx.diameter(G_clean)
            invariants['radius'] = nx.radius(G_clean)
        else:
            invariants['diameter'] = float('inf')
            invariants['radius'] = float('inf')

        degrees = dict(G_clean.degree())
        deg_vals = list(degrees.values())
        invariants['minimum_degree'] = min(deg_vals)
        invariants['maximum_degree'] = max(deg_vals)
        invariants['average_degree'] = sum(deg_vals) / n
        invariants['density'] = 2 * m / (n * (n - 1))

        # Indices topologiques
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

        # Invariants spectraux
        A = nx.to_numpy_array(G_clean)
        eig_A = np.linalg.eigvalsh(A)
        invariants['largest_eigenvalue'] = float(np.max(eig_A))

        L = nx.laplacian_matrix(G_clean).toarray().astype(float)
        eig_L = sorted(np.linalg.eigvalsh(L))
        invariants['second_smallest_laplace_eigenvalue'] = float(eig_L[1]) if len(eig_L) > 1 else 0.0

        if connected and n <= 60:
            dist = nx.floyd_warshall_numpy(G_clean)
            eig_D = np.linalg.eigvalsh(dist)
            invariants['largest_distance_eigenvalue'] = float(np.max(eig_D))
            avg_dists = dist.mean(axis=1)
            invariants['proximity'] = float(np.min(avg_dists))
            invariants['remoteness'] = float(np.max(avg_dists))
        else:
            invariants['largest_distance_eigenvalue'] = float('inf')
            invariants['proximity'] = float('inf')
            invariants['remoteness'] = float('inf')

        # Invariants combinatoires
        invariants['triangle_number'] = sum(nx.triangles(G_clean).values()) // 3

        cliques = list(nx.find_cliques(G_clean)) if n > 0 else [[]]
        invariants['clique_number'] = len(max(cliques, key=len)) if cliques else 0

        invariants['domination_number'] = len(nx.dominating_set(G_clean))
        invariants['matching_number'] = len(nx.max_weight_matching(G_clean, maxcardinality=True))

        # Independence number : maximum sur plusieurs tirages aléatoires
        best_indep = 0
        best_idom = float('inf')
        for _ in range(8):
            indep = nx.maximal_independent_set(G_clean)
            best_indep = max(best_indep, len(indep))
            best_idom = min(best_idom, len(indep))
        invariants['independence_number'] = best_indep
        invariants['vertex_cover_number'] = n - best_indep  # théorème de Gallai
        invariants['independent_domination_number'] = best_idom if best_idom != float('inf') else 0

        if connected and m > 0:
            invariants['total_domination_number'] = len(_greedy_total_dominating_set(G_clean))
        else:
            invariants['total_domination_number'] = 0

        if connected:
            invariants['node_connectivity'] = nx.node_connectivity(G_clean)
            invariants['edge_connectivity'] = nx.edge_connectivity(G_clean)
        else:
            invariants['node_connectivity'] = 0
            invariants['edge_connectivity'] = 0

    except Exception as e:
        print(f"Erreur lors du calcul des invariants : {e}")
    return invariants
