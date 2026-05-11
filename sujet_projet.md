### Analyse du Sujet : Réfutation Automatique de Conjectures en Théorie des Graphes

Ce document résume le projet "GraphBench Challenge" pour le Master 1 MIAGE, axé sur la réfutation de conjectures en théorie des graphes à l'aide de métaheuristiques et d'une architecture inspirée de FunSearch.

---

### 1. Contexte et Objectif Général

Le but du projet est de développer un programme capable de trouver automatiquement des **contre-exemples** à des conjectures en théorie des graphes.

Une conjecture est une affirmation sur une propriété supposée vraie pour une classe de graphes. Elle a souvent la forme :
`∀G ∈ C, A(G) ≤ f(B(G))`
Où :
-   `G` est un graphe.
-   `C` est une classe de graphes (ex: connexes, planaires, sans griffe).
-   `A(G)` et `B(G)` sont des **invariants** du graphe (ex: nombre de sommets, diamètre, connectivité).

Le programme doit générer des graphes, calculer leurs invariants et chercher efficacement ceux qui **violent** la conjecture (c'est-à-dire qui ne respectent pas l'inégalité). L'objectif est de maximiser un **score de violation**.

### 2. Le Projet en Deux Parties

#### Partie 1 : Construire une Première Heuristique
Cette partie consiste à implémenter une recherche locale simple mais fonctionnelle. L'algorithme doit :
1.  **Générer une population de graphes initiaux**.
2.  Entrer dans une boucle de recherche limitée dans le temps (60 secondes par conjecture).
3.  À chaque itération :
    -   Sélectionner un graphe candidat.
    -   Appliquer une **mutation locale** (ex: ajout/suppression d'arête ou de sommet).
    -   **Réparer** le graphe si la mutation lui a fait perdre une propriété requise (ex: s'il n'est plus connexe).
    -   Calculer son score de violation.
    -   Conserver le meilleur graphe trouvé.
4.  Si un graphe avec un score de violation strictement positif est trouvé, il s'agit d'un contre-exemple.

#### Partie 2 : Architecture Inspirée de FunSearch
L'objectif est d'améliorer la recherche en automatisant la découverte d'une meilleure fonction de score. Au lieu de se baser uniquement sur la violation, on cherche une fonction plus riche :
`F(G) = violation(G) + bonus(G) − penalty(G)`

Cette fonction doit guider la recherche vers des graphes prometteurs, même s'ils ne sont pas encore des contre-exemples. L'architecture proposée est la suivante :
1.  Un **Grand Modèle de Langage (LLM)** propose des fonctions de score en Python.
2.  Ces fonctions sont testées sur un ensemble de conjectures.
3.  Les plus performantes sont conservées.
4.  Le LLM reçoit les meilleures fonctions en retour pour proposer des variantes améliorées.
5.  Le processus est répété pour faire évoluer les fonctions de score.

### 3. Évaluation et Livrables

-   **Évaluation** : Les programmes sont évalués sur un benchmark de conjectures. Le score final est basé sur le temps de réfutation. Un contre-exemple non trouvé dans les 60 secondes imparties entraîne une pénalité. Le but est d'obtenir le **score le plus faible possible**.
-   **Livrables** :
    -   Un **dépôt GitHub** complet et bien structuré (code source, `README.md`, `requirements.txt`, etc.).
    -   Un **rapport de 5 pages** détaillant la démarche, l'heuristique, l'architecture FunSearch, les résultats et une discussion scientifique.

### 4. Points Clés et Contraintes

-   **Outils** : L'utilisation d'outils comme NetworkX, igraph et les IA génératives est encouragée.
-   **Interdictions** : Il est formellement interdit de coder en dur les contre-exemples connus ou de manipuler le benchmark.
-   **Invariants** : Le projet implique le calcul de nombreux invariants de graphes comme le diamètre, le rayon, la connectivité, la taille d'une clique maximum, etc.

En résumé, ce projet est un défi d'ingénierie algorithmique où il faut combiner des techniques de recherche locale, de l'optimisation et de l'intelligence artificielle pour résoudre un problème complexe de la théorie des graphes.
