SYSTEM_CONTEXT = """
Tu es un expert en théorie des graphes.

## Contexte
Notre solver cherche des contre-exemples à des conjectures en appliquant des mutations sur des graphes via un algorithme de recherche locale.
Nous voulons optimiser la fonction de score qui évalue les graphes pour guider la recherche vers des graphes prometteurs avant même qu'ils ne soient des contre-exemples.

La forme imposée de la fonction générée est :
```python
def heuristic_score(G, invariants, conjecture):
    violation = conjecture.violation(invariants)
    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    delta = invariants.get("delta", 0)
    Delta = invariants.get("Delta", 0)
    diam = invariants.get("diam", 0)
    gamma = invariants.get("gamma", 0)
    alpha = invariants.get("alpha", 0)
    tau = invariants.get("tau", 0)
    triangles = invariants.get("triangles", 0)
    
    # TON CODE ICI
    # retourne un score numérique à maximiser
    return violation
```

## Ta mission
Tu dois chercher automatiquement à remplacer le dernier `return violation` par une fonction plus efficace.
L'idée est de créer une fonction plus informative :
F(G) = violation + bonus(G) - penalty(G)
Tu peux utiliser les invariants déjà extraits, ou même utiliser `G` (le graphe NetworkX) pour extraire d'autres métriques.

Réponds uniquement par le bloc de code Python contenant la fonction `heuristic_score` complète.
"""

def build_initial_prompt():
    return SYSTEM_CONTEXT + """
Propose une première version intelligente de `heuristic_score`. 
Génère UNIQUEMENT le bloc de code python commençant par `def heuristic_score(G, invariants, conjecture):`.
"""

def build_iteration_prompt(best_functions):
    functions_block = ""
    for i, (code, perf, details) in enumerate(best_functions, start=1):
        functions_block += f"\n### Meilleur candidat {i} (Nombre de conjectures réfutées : {perf})\n```python\n{code}\n```\n"

    return SYSTEM_CONTEXT + f"""
## Fonctions actuelles les plus performantes :
{functions_block}

## Ta mission
Analyse ces résultats et propose une NOUVELLE variante de la fonction `heuristic_score` qui pourrait être encore meilleure pour guider la recherche.
Combine les bonnes idées, ajuste les poids, ou ajoute de nouveaux invariants.
Génère UNIQUEMENT le bloc de code python commençant par `def heuristic_score(G, invariants, conjecture):`.
"""
