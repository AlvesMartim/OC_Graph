# GraphBench Challenge — M1 MIAGE

Réfutation automatique de conjectures en théorie des graphes.

**Score actuel : 99/100 conjectures réfutées.**

---

## Structure du projet

```
experiments/
├── heuristique1.py     # Point d'entrée partie 1
└── heuristique2.py     # Point d'entrée partie 2
src/
├── heuristique1/       # Package partie 1 (recherche locale)
└── heuristique2/       # Package partie 2 (FunSearch LLM)
benchmark/
├── benchmark.xlsx      # 100 conjectures
└── results.json        # Résultats de la dernière exécution
.env                    # GEMINI_API_KEY (non versionné)
heuristique1.md         # Documentation détaillée de l'algorithme
```

---

## Installation

```bash
pip install -r requirements.txt
```

Dépendances : `pandas`, `networkx`, `numpy`, `openpyxl`, `google-genai`, `python-dotenv`

---

## Lancement

```bash
# Partie 1 — Recherche locale (résultats dans benchmark/results.json)
python experiments/heuristique1.py

# Partie 2 — FunSearch LLM (nécessite GEMINI_API_KEY dans .env)
python experiments/heuristique2.py
```

---

## Partie 1 — Recherche locale évolutionnaire

Voir [heuristique1.md](heuristique1.md) pour la documentation complète.

L'algorithme fonctionne en 3 phases pour chaque conjecture (budget : 60s + pénalité 120s si échec) :

1. **Passe atlas** (5s) : énumération de graphes connus — atlas NetworkX, arbres non-isomorphes, familles paramétriques (chemins, cliques, K_n+bras, bipartis, etc.)
2. **Population initiale** : 10 graphes adaptés à la classe (`connected`, `tree`, `claw_free`)
3. **Recherche locale** (60s) : tournoi → mutation ciblée → réparation → évaluation du score de violation

---

## Partie 2 — FunSearch (LLM)

Un LLM (Gemini 2.5 Flash Lite) génère et améliore itérativement une fonction de score :

```
F(G) = violation(G) + bonus(G) − penalty(G)
```

5 itérations : génération → évaluation sur 20 conjectures × 10s → feedback ciblé sur les échecs → nouvelle génération.

Configurer la clé API dans `.env` :
```
GEMINI_API_KEY=<clé depuis aistudio.google.com>
```
