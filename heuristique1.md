# Heuristique 1 — Recherche locale évolutionnaire

## Objectif

Trouver des **contre-exemples** à des conjectures de la forme `Y(G) ≤ f(X(G))` ou `Y(G) ≥ f(X(G))`.

Un contre-exemple est un graphe G tel que la conjecture est violée :

```
violation = Y(G) - f(X(G))   si signe ≤
violation = f(X(G)) - Y(G)   si signe ≥

f(X) = intercept + c₁·X + c₂·X² + c₃·X³   (coefficients en fractions rationnelles)
```

Un score > 0 signifie que G est un contre-exemple.

---

## Score final

```
Score = Σ temps_i    avec temps_i = temps réel si réfutée, 120s sinon
```

**Plus bas = meilleur.** Minimum théorique = 0s.

---

## Algorithme en 3 phases

### Phase 1 — Passe atlas (5 secondes max)

Énumération rapide de graphes structurés connus :

| Source | Contenu |
|---|---|
| Atlas NetworkX | 1 252 graphes à ≤ 7 sommets |
| Arbres non-isomorphes | 8–12 sommets (si classe `tree`) |
| Familles paramétriques | Chemins, cycles, étoiles, K_n, roues, chenilles, double-étoiles, bipartis complets, **K_n + bras**, compléments de chemins, graphe de Petersen — pour n de 8 à 25 |

La famille **K_n + bras** (clique K_n avec un chemin attaché) est claw-free et permet de réfuter les conjectures impliquant `remoteness` et `radius`.

Si un contre-exemple est trouvé, la recherche s'arrête immédiatement.

### Phase 2 — Population initiale

10 graphes générés selon la classe de la conjecture :

- **`tree`** : arbres aléatoires
- **`claw_free`** : graphes complets ou denses réparés
- **`connected`** : graphes aléatoires reconnectés
- Pour les conjectures impliquant `proximity` ou `remoteness` : seeds structurées (double-étoiles déséquilibrées, brooms, K_n + bras)

### Phase 3 — Recherche locale (60 secondes max)

```
tant que temps < 60s :
    1. Sélection par tournoi (k=3)
    2. Mutation ciblée ou aléatoire
    3. Réparation selon la classe
    4. Évaluation du score de violation
    5. Mise à jour de la population si amélioration
```

---

## Mutations

### Ciblées (70% du temps)

L'invariant Y et le sens de l'inégalité déterminent la mutation :

| Invariant Y | Direction | Mutation |
|---|---|---|
| `triangle_number` | ↑ | Arête entre deux voisins non connectés |
| `triangle_number` | ↓ | Retirer une arête d'un triangle |
| `clique_number` | ↑ / ↓ | Étendre / casser la clique maximale |
| `diameter` / `radius` | ↑ | Ajouter une feuille à un sommet extrême |
| `diameter` / `radius` | ↓ | Raccourci entre sommets distants |
| `matching_number` | ↑ / ↓ | Arête entre non-couplés / retirer du couplage |
| `maximum_degree` | ↑ / ↓ | Connecter / déconnecter le sommet de degré max |
| `proximity` | ↑ | Relier le sommet de transmission max au centre |
| `proximity` | ↓ | Ajouter un sommet pendant au sommet le plus éloigné |
| `independence_number` | ↑ / ↓ | Retirer / ajouter une arête |

### Aléatoires (30% du temps)

Ajout/suppression d'arête ou de sommet — pour maintenir la diversité.

---

## Diversification

| Mécanisme | Seuil | Action |
|---|---|---|
| Liste tabou | — | Évite de revisiter les graphes déjà explorés (max 5 000, hashés en graph6) |
| Kick mutations | 100 itérations sans amélioration | 4 mutations consécutives pour franchir un plateau |
| Redémarrage complet | 500 itérations sans amélioration | Remplace toute la population par de nouveaux graphes |

---

## Réparations

Après chaque mutation, le graphe est corrigé si la classe est violée :

| Classe | Réparation |
|---|---|
| `connected` | Connexion des composantes par ajout d'arêtes |
| `tree` | Arbre couvrant (suppression des cycles) |
| `claw_free` | Suppression des griffes K₁,₃ induites |

---

## Calcul des invariants

Calcul **paresseux** : seuls X, Y et les basiques sont calculés à chaque itération.

| Famille | Invariants |
|---|---|
| Basiques (toujours) | `order`, `size`, `density`, `min/max/avg_degree`, indices de Zagreb, Randić, harmonique |
| Distances | `diameter`, `radius`, `proximity`, `remoteness`, `largest_distance_eigenvalue` |
| Spectraux | `largest_eigenvalue`, `second_smallest_laplace_eigenvalue` |
| Combinatoires | `triangle_number`, `clique_number`, `domination_number`, `total_domination_number`, `independence_number`, `independent_domination_number`, `vertex_cover_number`, `matching_number`, `node_connectivity`, `edge_connectivity` |

---

## Structure du code

```
src/heuristique1/
├── search.py      # Boucle principale, sélection, seeds, violation_score
├── mutations.py   # Mutations ciblées et aléatoires
├── invariants.py  # Calcul lazy des 25 invariants
├── repair.py      # Réparations selon la classe
├── atlas.py       # Familles de graphes connus + paramétriques
└── utils.py       # Parsing fractions, polynômes, sous-groupes
```

---

## Résultats

**99/100 conjectures réfutées.** La conjecture n°39 (ID 6574) n'est pas réfutable : il s'agit d'un théorème vrai pour les graphes sans griffe — `α(G) ≤ 1 + γ_t(G)` est démontré dans la littérature.
