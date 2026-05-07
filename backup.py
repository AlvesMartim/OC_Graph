
import pandas as pd
import networkx as nx
import time
import random

# -----------------------------------------------------------------------------
# Fonctions de calcul des invariants (à compléter)
# -----------------------------------------------------------------------------

def compute_invariants(G):
    """Calcule les invariants nécessaires pour un graphe G."""
    invariants = {}
    try:
        # Nettoyage de sécurité: on supprime les boucles (self-loops) qui invalident certains calculs (ex: clique, indep_set)
        G_clean = G.copy()
        G_clean.remove_edges_from(nx.selfloop_edges(G_clean))
        
        invariants['order'] = G_clean.number_of_nodes()
        invariants['size'] = G_clean.number_of_edges()
        if nx.is_connected(G_clean):
            invariants['diameter'] = nx.diameter(G_clean)
            invariants['radius'] = nx.radius(G_clean)
        else:
            invariants['diameter'] = float('inf')
            invariants['radius'] = float('inf')
        
        degrees = [d for n, d in G_clean.degree()]
        if degrees:
            invariants['minimum_degree'] = min(degrees)
            invariants['maximum_degree'] = max(degrees)
            invariants['average_degree'] = sum(degrees) / len(degrees)
        else:
            invariants['minimum_degree'] = 0
            invariants['maximum_degree'] = 0
            invariants['average_degree'] = 0

        # Placeholder pour les autres invariants (plus complexes)
        invariants['triangle_number'] = sum(nx.triangles(G_clean).values()) // 3
        invariants['clique_number'] = len(max(nx.find_cliques(G_clean), key=len)) if G_clean.number_of_nodes() > 0 else 0
        invariants['domination_number'] = len(nx.dominating_set(G_clean)) if G_clean.number_of_nodes() > 0 else 0
        invariants['independence_number'] = len(nx.maximal_independent_set(G_clean)) if G_clean.number_of_nodes() > 0 else 0
        invariants['vertex_cover_number'] = invariants['order'] - invariants['independence_number'] # Théorème de Gallai
        invariants['matching_number'] = len(nx.max_weight_matching(G_clean, maxcardinality=True))
        if nx.is_connected(G_clean):
            invariants['node_connectivity'] = nx.node_connectivity(G_clean)
            invariants['edge_connectivity'] = nx.edge_connectivity(G_clean)
        else:
            invariants['node_connectivity'] = 0
            invariants['edge_connectivity'] = 0

    except Exception as e:
        print(f"Erreur lors du calcul des invariants : {e}")
    return invariants

# -----------------------------------------------------------------------------
# Fonctions de l'heuristique
# -----------------------------------------------------------------------------

def generate_initial_graphs(conjecture, num_graphs=10):
    """Génère une population de graphes initiaux."""
    # Pour l'instant, génère des graphes aléatoires simples
    population = []
    for _ in range(num_graphs):
        n = random.randint(5, 20)
        p = random.uniform(0.2, 0.5)
        G = nx.gnp_random_graph(n, p)
        population.append(G)
    return population

def select_candidate(population):
    """Sélectionne un graphe candidat dans la population."""
    # Sélection aléatoire pour commencer
    return random.choice(population)

def mutate(G):
    """Applique une mutation locale à un graphe G."""
    H = G.copy()
    
    mutations = ['add_edge', 'remove_edge', 'remove_node']
    # On limite la taille des graphes générés pour éviter des calculs trop longs (ex: connectivité)
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
            u, v = random.choice(edges)
            H.remove_edge(u, v)
    elif mutation_type == 'add_node':
        new_node = max(H.nodes()) + 1 if H.number_of_nodes() > 0 else 0
        H.add_node(new_node)
        if H.number_of_nodes() > 1:
            target_node = random.choice([n for n in H.nodes() if n != new_node])
            H.add_edge(new_node, target_node)
    elif mutation_type == 'remove_node':
        nodes = list(H.nodes())
        if nodes:
            node_to_remove = random.choice(nodes)
            H.remove_node(node_to_remove)
            
    return H

def repair_if_needed(H, graph_class):
    """Répare le graphe H s'il ne respecte plus la classe requise."""
    # Placeholder : pour l'instant, on ne fait rien
    if graph_class == 'Gconnected' and not nx.is_connected(H):
        # Simple réparation : on reconnecte les composantes
        components = list(nx.connected_components(H))
        if len(components) > 1:
            for i in range(len(components) - 1):
                u = random.choice(list(components[i]))
                v = random.choice(list(components[i+1]))
                H.add_edge(u, v)
    # Ajouter des réparations pour d'autres classes (planar, bipartite, etc.)
    return H

def violation_score(invariants, conjecture):
    """Calcule le score de violation pour une conjecture donnée."""
    try:
        # Forme générale: Y <= (ou >=) degree * X + intercept
        # On va parser ça de facon simple en utilisant X et Y.
        # Par defaut A <= B devient A - B <= 0. La violation > 0.
        X_name = conjecture['X']
        Y_name = conjecture['Y']
        
        X_val = float(invariants.get(X_name, 0))
        Y_val = float(invariants.get(Y_name, 0))
        
        # S'il y a un Degree ou Intercept spécifique:
        try:
            degree_str = str(conjecture.get('Degree', 1)).strip()
            degree = float(degree_str) if degree_str and degree_str != 'nan' else 1.0
        except ValueError:
            degree = 1.0
            
        try:
            intercept_str = str(conjecture.get('Intercept', 0)).strip()
            intercept = float(intercept_str) if intercept_str and intercept_str != 'nan' else 0.0
        except ValueError:
            intercept = 0.0
        
        # f(X)
        f_X = degree * X_val + intercept
        
        if conjecture['Sign'] == '<=':
            # Y <= f_X  =>  violation = Y - f_X
            return Y_val - f_X
        elif conjecture['Sign'] == '>=':
            # Y >= f_X  =>  violation = f_X - Y
            return f_X - Y_val
        elif conjecture['Sign'] == '<':
            return Y_val - f_X
        elif conjecture['Sign'] == '>':
            return f_X - Y_val
        else:
            return -1

    except Exception as e:
        print(f"Erreur dans le calcul du score : {e}")
        return -float('inf')


def counterexample_found(G, invariants, conjecture, score):
    """Affiche les informations sur le contre-exemple trouvé."""
    print("\n" + "="*50)
    print("🎉 Contre-exemple trouvé ! 🎉")
    print(f"Conjecture: {conjecture['Conjecture']}")
    print(f"Graphe (graph6): {nx.to_graph6_bytes(G).decode('ascii').strip()}")
    print(f"Ordre: {invariants.get('order', 'N/A')}, Taille: {invariants.get('size', 'N/A')}")
    print(f"Invariants concernés: {conjecture['X']}={invariants.get(conjecture['X'], 'N/A')}, {conjecture['Y']}={invariants.get(conjecture['Y'], 'N/A')}")
    print(f"Score de violation: {score:.4f}")
    print("="*50 + "\n")
    return G # On retourne le graphe pour l'arrêter

def search_failed():
    """Indique que la recherche a échoué dans le temps imparti."""
    # print("...recherche infructueuse dans le temps imparti.")
    return None

# -----------------------------------------------------------------------------
# Boucle de recherche principale
# -----------------------------------------------------------------------------

def run_heuristic(conjecture):
    """Exécute l'heuristique pour une seule conjecture."""
    start_time = time.time()
    
    population = generate_initial_graphs(conjecture)
    best_graph = None
    best_score = -float('inf')
    
    time_elapsed = 0
    
    while time_elapsed < 60:
        G = select_candidate(population)
        H = mutate(G)
        
        # La classe du graphe est dans la colonne 'Subgroup'
        graph_class = conjecture.get('Subgroup')
        if graph_class:
            H = repair_if_needed(H, graph_class)
        
        # On ne calcule les invariants que si le graphe est valide
        if H.number_of_nodes() > 0:
            invariants = compute_invariants(H)
            score = violation_score(invariants, conjecture)
            
            if score > best_score:
                best_score = score
                best_graph = H
                # On met à jour la population avec les meilleurs graphes
                population.append(H)
                population = sorted(population, key=lambda g: violation_score(compute_invariants(g), conjecture), reverse=True)[:10]


            if score > 0:
                return counterexample_found(H, invariants, conjecture, score)
        
        time_elapsed = time.time() - start_time

    return search_failed()


if __name__ == '__main__':
    # Chargement du benchmark
    try:
        benchmark_df = pd.read_excel("benchmark.xlsx")
        print(f"{len(benchmark_df)} conjectures chargées.")
    except FileNotFoundError:
        print("Erreur : Le fichier 'benchmark.xlsx' est introuvable.")
        exit()

    # On itère sur chaque conjecture du benchmark
    for index, conjecture_row in benchmark_df.iterrows():
        print(f"\n--- Traitement de la conjecture {conjecture_row['Conjecture ID']}: {conjecture_row['Conjecture']} ---")
        result = run_heuristic(conjecture_row)
        if result is None:
            print("Aucun contre-exemple trouvé en 60 secondes.")


