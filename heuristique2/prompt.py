from fractions import Fraction
import ast

INVARIANTS_LIST = """
- order, size, density, diameter, radius
- minimum_degree, maximum_degree, average_degree
- first_zagreb_index, second_zagreb_index, randic_index, harmonic_index
- largest_eigenvalue, second_smallest_laplace_eigenvalue
- largest_distance_eigenvalue, proximity, remoteness
- triangle_number, clique_number, domination_number, total_domination_number
- independence_number, independent_domination_number
- vertex_cover_number, matching_number, node_connectivity, edge_connectivity
"""

BASELINE_FUNCTION = '''def score(invariants: dict, conjecture: dict) -> float:
    """Fonction de base : violation pure sans guidage."""
    from fractions import Fraction
    import ast

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
        return Y_val - f_X
    else:
        return f_X - Y_val'''

SYSTEM_CONTEXT = """
Tu es un expert en théorie des graphes et en optimisation combinatoire.

## Contexte

Une recherche locale cherche des contre-exemples à des conjectures de la forme :
  Y(G) <= f(X(G))   ou   Y(G) >= f(X(G))

À chaque itération, un graphe muté est évalué par une fonction `score`. La recherche
suit le gradient de ce score : elle explore les graphes qui maximisent cette valeur.

Un score > 0 signifie que le graphe viole la conjecture : c'est un contre-exemple.

## Invariants disponibles dans `invariants` (dict)

{invariants}

## Structure de `conjecture` (dict)

- 'X'           : nom de l'invariant en entrée (ex: 'maximum_degree')
- 'Y'           : nom de l'invariant cible (ex: 'triangle_number')
- 'Sign'        : '<=' ou '>='
- 'Coefficients': liste de coefficients ['c1', 'c2', 'c3'] tels que f(X) = intercept + c1*X + c2*X² + c3*X³
- 'Intercept'   : constante (fraction string, ex: '-1/6')
- 'Subgroup'    : classe du graphe (ex: "['connected']", "['claw_free', 'connected']", "['connected', 'tree']")

## Fonction de base (à améliorer)

La fonction suivante calcule la violation pure. Elle fonctionne mais ne guide pas
la recherche quand la violation est encore négative (avant de trouver un contre-exemple) :

```python
{baseline}
```

## Ce que tu dois faire

Écris une version AMÉLIORÉE de cette fonction qui guide mieux la recherche locale.
Quelques idées de guidage (bonus/pénalités) à explorer :

- **Amplifier** la violation selon les invariants structurels du graphe
- **Bonus** si le graphe est dans une zone prometteuse (ex: forte densité pour maximiser les triangles)
- **Pénalité** pour les graphes trop grands (calculs lents) ou triviaux
- **Normalisation** par ordre du graphe pour comparer des graphes de tailles différentes
- **Exploiter la classe** : un graphe claw_free a des contraintes sur ses cliques, un arbre a diamètre = order-1, etc.
- **Bonus de progression** : si Y(G) est déjà grand par rapport à f(X(G)), amplifier

## Contraintes absolues

- Signature exacte : `def score(invariants: dict, conjecture: dict) -> float`
- Ne jamais retourner float('inf') ou float('nan')
- Gérer les divisions par zéro et les invariants absents avec `.get(..., 0)`
- Inclure `from fractions import Fraction` et `import ast` dans le corps de la fonction
- Le score doit rester > 0 si et seulement si c'est un contre-exemple

## Démarche attendue

1. Analyse brièvement la structure mathématique de la conjecture (≤ ou ≥, linéaire ou polynomiale)
2. Identifie quels invariants secondaires peuvent indiquer qu'on approche d'une violation
3. Écris la fonction avec des commentaires expliquant chaque choix
""".format(invariants=INVARIANTS_LIST, baseline=BASELINE_FUNCTION)


def build_initial_prompt():
    return SYSTEM_CONTEXT + """
## Itération 1 — Première tentative

C'est la première itération. Pars de la fonction de base et propose une amélioration
originale et bien motivée. Sois créatif sur les bonus/pénalités.
"""


def build_iteration_prompt(best_functions, failed_conjectures=None):
    """Construit le prompt avec les meilleures fonctions et les conjectures échouées."""
    functions_block = ""
    for i, (code, perf, details) in enumerate(best_functions, start=1):
        functions_block += f"\n### Fonction {i} — {perf} conjectures réfutées\n"
        if details:
            solved = [str(c) for c in details.get('solved', [])]
            failed = [str(c) for c in details.get('failed', [])]
            if solved:
                functions_block += f"Réfutées : {', '.join(solved)}\n"
            if failed:
                functions_block += f"Échouées : {', '.join(failed)}\n"
        functions_block += f"```python\n{code}\n```\n"

    failed_block = ""
    if failed_conjectures:
        failed_block = f"\nConjectures jamais réfutées par aucune fonction : {', '.join(str(c) for c in failed_conjectures)}\n"

    return SYSTEM_CONTEXT + f"""
## Résultats des itérations précédentes
{functions_block}
{failed_block}

## Ta mission

- Identifie ce qui distingue les conjectures réfutées de celles qui ont échoué
- Propose une NOUVELLE fonction qui corrige les faiblesses observées
- Tu peux t'inspirer des meilleures fonctions mais tu dois innover sur au moins un point
- Explique ta démarche avant d'écrire le code
"""
