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

SYSTEM_CONTEXT = """
Tu es un expert en théorie des graphes. Tu dois écrire une fonction Python qui guide
une recherche locale pour trouver des contre-exemples à des conjectures de graphes.

Une conjecture a la forme : Y(G) <= f(X(G))  ou  Y(G) >= f(X(G))
Les invariants disponibles dans le dictionnaire `invariants` sont :
{invariants}

La conjecture est un dictionnaire avec les clés :
- 'X' : nom de l'invariant en entrée
- 'Y' : nom de l'invariant cible
- 'Sign' : '<=' ou '>='
- 'Coefficients' : liste de coefficients du polynôme (fractions sous forme de strings)
- 'Intercept' : constante (fraction sous forme de string)
- 'Subgroup' : classe du graphe (ex: "['connected']", "['claw_free', 'connected']")

Tu dois écrire UNE SEULE fonction Python avec cette signature exacte :

```python
def score(invariants: dict, conjecture: dict) -> float:
    # violation de base : positif = contre-exemple trouvé
    ...
    return float
```

La fonction doit retourner un score PLUS ÉLEVÉ pour les graphes plus proches d'un contre-exemple.
Un score > 0 signifie que le graphe est un contre-exemple.
Tu peux ajouter des bonus/pénalités pour guider la recherche.
Ne jamais retourner float('inf') ou float('nan').
""".format(invariants=INVARIANTS_LIST)


def build_initial_prompt():
    return SYSTEM_CONTEXT + """
C'est la première itération. Propose une fonction de score originale et bien motivée.
Explique brièvement ta stratégie puis écris le code.
"""


def build_iteration_prompt(best_functions):
    """Construit le prompt avec les meilleures fonctions trouvées."""
    functions_block = ""
    for i, (code, perf) in enumerate(best_functions, start=1):
        functions_block += f"\n### Fonction {i} — score : {perf:.1f} conjectures réfutées\n"
        functions_block += f"```python\n{code}\n```\n"

    return SYSTEM_CONTEXT + f"""
Voici les meilleures fonctions trouvées jusqu'ici :
{functions_block}

En t'inspirant de ces fonctions, propose une NOUVELLE variante améliorée.
Identifie ce qui fonctionne bien, corrige les faiblesses, et innove.
Explique brièvement ta démarche puis écris le code.
"""
