# GraphBench Project

Ce dépôt contient le code source, les expériences et les résultats de notre projet.

## Structure du projet

- `src/` : Contient le code source principal (les heuristiques : `heuristique1`, `heuristique2`).
- `benchmark/` : Contient les données d'évaluation (ex: `benchmark.xlsx`).
- `experiments/` : Contient les scripts pour lancer les expériences (`heuristique1.py`, `heuristique2.py`).
- `results/` : Contient les résultats obtenus lors des expérimentations.
- `report.pdf` : Le rapport final du projet.

## Installation

Installez les dépendances requises via la commande suivante :

```bash
pip install -r requirements.txt
```

## Lancement des expériences

Depuis la racine du projet, exécutez les scripts suivants (assurez-vous que Python trouve vos modules dans `src/` si nécessaire) :

```bash
# Exemple d'exécution
python experiments/heuristique1.py
```