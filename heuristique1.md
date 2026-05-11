# Heuristique 1 — Recherche locale évolutionnaire

## Objectif

Trouver des **contre-exemples** à des conjectures de la forme :

```
∀G ∈ C,  Y(G) ≤ f(X(G))
```

Un contre-exemple est un graphe G tel que `Y(G) > f(X(G))` — il **viole** la conjecture.

---

## Score de violation

Le score mesure à quel point un graphe viole la conjecture :

```
f(X) = intercept + c₁·X + c₂·X² + c₃·X³

violation = Y(G) - f(X(G))   si signe ≤
violation = f(X(G)) - Y(G)   si signe ≥
```

Un score > 0 signifie que le graphe est un contre-exemple.

---

## Algorithme

### 1. Passe Atlas (5 secondes)

Avant la recherche locale, l'algorithme énumère des graphes connus :
- **1 252 graphes** de l'atlas NetworkX (≤ 7 sommets)
- Arbres non-isomorphes à 8–12 sommets (si la classe est `tree`)

Si un contre-exemple est trouvé parmi ces graphes, la recherche s'arrête immédiatement.

### 2. Population initiale

10 graphes générés aléatoirement, adaptés à la classe de la conjecture :

| Classe | Génération |
|---|---|
| `tree` | `nx.random_tree(n)` |
| `claw_free` | Graphe complet ou graphe dense réparé |
| `connected` | Graphe aléatoire reconnecté |

### 3. Boucle de recherche (60 secondes max)

```
tant que temps < 60s :
    1. Sélection par tournoi (k=3) → meilleur parmi 3 graphes
    2. Mutation → modification du graphe
    3. Réparation → respect de la classe
    4. Évaluation → calcul du score de violation
    5. Mise à jour de la population si amélioration
```

---

## Mutations

### Mutations ciblées (70% du temps)

Selon l'invariant Y de la conjecture et le sens de l'inégalité, une mutation adaptée est choisie :

| Invariant Y | Augmenter | Diminuer |
|---|---|---|
| `triangle_number` | Arête entre deux voisins | Retirer arête d'un triangle |
| `clique_number` | Étendre la clique max | Casser une arête interne |
| `diameter` | Ajouter une feuille | Raccourci entre sommets distants |
| `matching_number` | Arête entre non-couplés | Retirer une arête du couplage |
| `maximum_degree` | Connecter le sommet le plus connecté | Retirer une arête incidente |
| `independence_number` | Retirer une arête | Ajouter une arête |

### Mutations aléatoires (30% du temps)

- Ajout / suppression d'arête
- Ajout / suppression de sommet

---

## Diversification

### Liste tabou
Chaque graphe visité est hashé en format graph6 et mis en liste noire (max 5 000 entrées) pour éviter de revisiter les mêmes graphes.

### Kick mutations
Après **100 itérations sans amélioration** : 4 mutations consécutives pour sauter un plateau local.

### Redémarrage complet
Après **500 itérations sans amélioration** : la population entière est remplacée par de nouveaux graphes aléatoires.

---

## Réparations

Après chaque mutation, le graphe est réparé si nécessaire :

| Classe | Réparation |
|---|---|
| `connected` | Connexion des composantes par ajout d'arêtes |
| `tree` | Calcul de l'arbre couvrant (suppression des cycles) |
| `claw_free` | Suppression des griffes K₁,₃ induites |

---

## Invariants calculés

L'évaluation est **paresseuse** : seuls les invariants X et Y de la conjecture sont calculés (+ les basiques toujours nécessaires), réduisant le temps de calcul.

| Famille | Invariants |
|---|---|
| Basiques (toujours) | `order`, `size`, `density`, `min/max/avg_degree`, indices de Zagreb, Randić, harmonique |
| Distances | `diameter`, `radius` |
| Spectraux | `largest_eigenvalue`, `second_smallest_laplace_eigenvalue`, `largest_distance_eigenvalue`, `proximity`, `remoteness` |
| Combinatoires | `triangle_number`, `clique_number`, `domination_number`, `total_domination_number`, `independence_number`, `independent_domination_number`, `vertex_cover_number`, `matching_number`, `node_connectivity`, `edge_connectivity` |

---

## Score final (évaluation)

Le score est la **somme des temps de réfutation** sur les 100 conjectures :

```
Score = Σ temps_i    avec temps_i = temps réel si réfutée, 60s sinon
```

**Plus bas = meilleur.** Minimum théorique = 0s (toutes réfutées instantanément).

---

## Structure du code

```
src/heuristique1/
├── __init__.py       # Expose run_heuristic()
├── search.py         # Boucle principale, sélection, violation_score
├── mutations.py      # Mutations ciblées et aléatoires
├── invariants.py     # Calcul lazy des 25 invariants
├── repair.py         # Réparations selon la classe
├── atlas.py          # Énumération des petits graphes connus
└── utils.py          # Parsing fractions, polynômes, sous-groupes
```
