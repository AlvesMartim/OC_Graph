from fractions import Fraction
import ast

INVARIANTS_LIST = """
- order (ou n), size (ou m), density, diameter, radius
- minimum_degree (ou delta), maximum_degree (ou Delta), average_degree
- first_zagreb_index, second_zagreb_index, randic_index, harmonic_index
- largest_eigenvalue, second_smallest_laplace_eigenvalue
- largest_distance_eigenvalue, proximity, remoteness
- triangle_number (ou triangles), clique_number, domination_number (ou gamma), total_domination_number
- independence_number (ou alpha), independent_domination_number
- vertex_cover_number (ou tau), matching_number, node_connectivity, edge_connectivity
"""

BASELINE_FUNCTION = '''def heuristic_score(G, invariants: dict, conjecture: dict) -> float:
    """Fonction de base : violation pure."""
    from fractions import Fraction
    import ast
    import math

    X_val = float(invariants.get(conjecture['X'], 0))
    Y_val = float(invariants.get(conjecture['Y'], 0))

    coeffs_raw = conjecture.get('Coefficients', '')
    intercept_raw = str(conjecture.get('Intercept', 0))

    try:
        coeffs = ast.literal_eval(coeffs_raw) if isinstance(coeffs_raw, str) else coeffs_raw
        intercept = float(Fraction(intercept_raw))
        f_X = intercept + sum(float(Fraction(c)) * (X_val ** (i + 1)) for i, c in enumerate(coeffs))
    except Exception:
        f_X = float(conjecture.get('Degree', 1)) * X_val

    if conjecture['Sign'] in ('<=', '<'):
        violation = Y_val - f_X
    else:
        violation = f_X - Y_val
        
    return violation'''

SYSTEM_CONTEXT = """
Tu es un expert en théorie des graphes et en apprentissage automatique.

## Contexte

Une recherche locale cherche des contre-exemples à des conjectures (Y <= f(X) ou Y >= f(X)).
L'idée est de guider le parcours en maximisant une fonction de ce type :
  F(G) = violation(G) + bonus(G) - penalty(G)

Un score de F(G) > 0 dans notre évaluateur confirme un contre-exemple. 
Notre but absolu : concevoir la fonction F(G) la plus intelligente possible pour que la recherche trouve les contre-exemples TRÈS RAPIDEMENT. Le critère d'évaluation est le temps (coût).

## Invariants disponibles dans `invariants` (dict)

{invariants}

## Structure de `conjecture` (dict)

- 'X'           : nom de l'invariant en entrée (ex: 'maximum_degree')
- 'Y'           : nom de l'invariant cible (ex: 'triangle_number')
- 'Sign'        : '<=' ou '>='
- 'Coefficients': liste ['c1', 'c2', 'c3'] tels que f(X) = intercept + c1*X + c2*X² + c3*X³
- 'Subgroup'    : classe du graphe (ex: "['connected']", "['claw_free']")

## Fonction de base (à remplacer)

```python
{baseline}
```
Ton but est de remplacer le `return violation` final par une formule beaucoup plus puissante.

## 🛑 CONSIGNES CRITIQUES POUR OBTENIR UN BON RATIO (À LIRE ABSOLUMENT) 🛑

NE TE CONTENTE PAS d'une simple combinaison linéaire type `(10 * violation + 0.3 * diam - 0.2 * n)`. C'est trop basique et les performances stagnent !

POUR GAGNER :
1. **Utilise des non-linéarités :** 
   - `math.exp(violation)` pour exploser le score dès qu'on s'approche d'une violation (violation proche de 0).
   - `math.log(n)` pour pénaliser les très grands graphes de manière douce.
   - `math.tanh` ou `abs()` ou des carrés `**2` pour les densités.
2. **Utilise des ratios malins :** `alpha / n`, `Delta / n`, `2*m / (n*(n-1))`, `tau / alpha`. Les invariants bruts dépendent trop de la taille du graphe.
3. **Exploite la topologie selon les cas :** 
   - Si un graphe approche la violation, le pousser vers des structures extrêmes aide souvent (ex: densifier via `clique_number`, ou étirer via `diameter`).
4. **Cible les conjectures difficiles :** Regarde dans le prompt les conjectures qui "échouent" et invente une logique conditionnelle (`if`) ou mathématique pour les résoudre spécifiquement.

## Contraintes absolues

- Signature exacte : `def heuristic_score(G, invariants: dict, conjecture: dict) -> float`
- Gérer TOUJOURS les invariants absents ou les divisions par zéro avec `.get(..., 0)` ou des `try/except`
- Gérer les `math.exp` pour qu'ils ne fassent pas d'OverflowError (clamp avec `min(valeur, 100)` par exemple).
- Le paramètre G est gardé pour la signature mais tu dois utiliser principalement `invariants`.
""".format(invariants=INVARIANTS_LIST, baseline=BASELINE_FUNCTION)


def build_initial_prompt():
    return SYSTEM_CONTEXT + """
## Itération 1 — Première tentative

Propose une fonction `heuristic_score` ultra-créative. Utilise des ratios, des fonctions mathématiques non-linéaires (math.exp, math.log) pour guider le gradient avec force !
"""


def build_iteration_prompt(best_functions, failed_conjectures=None):
    """Construit le prompt avec les meilleures fonctions et les conjectures échouées."""
    functions_block = ""
    for i, (code, perf, details) in enumerate(best_functions, start=1):
        functions_block += f"\n### Fonction {i} — Réfutées: {perf}\n"
        functions_block += f"```python\n{code}\n```\n"

    failed_block = ""
    if failed_conjectures:
        failed_block = f"\n⚠️ CONJECTURES QUI RÉSISTENT ENCORE : {', '.join(str(c) for c in failed_conjectures)}\nTrouve une structure mathématique radicalement différente pour les atteindre !\n"

    return SYSTEM_CONTEXT + f"""
## Résultats des itérations précédentes
{functions_block}
{failed_block}

## Ta mission
- Ta précédente fonction était bien, mais trop linéaire !
- Invente de **nouveaux ratios** ou des **fonctions exponentielles/logarithmiques** pour guider le score de manière non linéaire.
- Fais baisser le coût temporel global !
"""