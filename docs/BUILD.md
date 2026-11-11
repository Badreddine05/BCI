# Installation, tests et reproduction

Python **3.13** est la version validée. Les trois bibliothèques numériques directes sont épinglées dans `pyproject.toml`. Le notebook historique n’est pas un prérequis d’exécution.

```sh
python -m venv .venv
# Linux/macOS : source .venv/bin/activate
# PowerShell : .venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m pytest -q
```

Les tests utilisent de petits signaux synthétiques et un MAT temporaire. Ils ne téléchargent pas le jeu EEG et ne nécessitent pas d’accès réseau. Ils contrôlent aussi que les métriques versionnées se réconcilient avec les matrices de confusion.

## Recalculer les résultats

```sh
# Premier essai : une personne, sortie séparée pour conserver le rapport complet
bci-lab --subjects 1 --download --output data/cache/subject1.json

# Rapport complet : neuf participants, environ 780 Mo de fichiers originaux
bci-lab --download

# Réutiliser les fichiers locaux sans réseau
bci-lab
```

L’exécution complète écrit `web/data/benchmark.json` et actualise `data/sources.json`. Les fichiers originaux sont conservés dans `data/raw/`, ignoré par Git. Les empreintes de sources déjà connues sont vérifiées ; une différence interrompt le calcul au lieu de remplacer silencieusement la référence. Le téléchargement se fait dans un fichier temporaire puis est renommé à sa fin. Une erreur de fichier, de label, de fenêtre ou de somme de contrôle est explicite.

Les calculs sont déterministes avec les versions épinglées. Des différences numériques faibles peuvent subsister entre bibliothèques BLAS ou plateformes. `generated_at` reflète la date réelle de chaque exécution ; il n’est donc pas identique d’un rapport à l’autre.

## Bibliothèque

```python
from pathlib import Path
from bci_lab.data import load_session
from bci_lab.evaluation import evaluate_pair

train = load_session(Path("data/raw/A01T.mat"), 1, "T")
test = load_session(Path("data/raw/A01E.mat"), 1, "E")
results = evaluate_pair(train, test)
```

Les fonctions d’exploration corrigées sont dans `bci_lab.analysis` : `RegularizedQDA`, `sliding_correlations` et `reconstruct_sparse_dct`. Elles ont leurs tests propres ; elles ne sont pas incluses comme modèles supplémentaires du benchmark publié.

## Frontend et intégration

Le contrat des données et les règles d’interprétation sont dans [FRONTEND_HANDOFF.md](../FRONTEND_HANDOFF.md). Pour actualiser les résultats, remplacer uniquement `web/data/benchmark.json` par la sortie validée du pipeline, en conservant les fichiers de présentation.

## CI

La CI installe les dépendances, compile les modules Python et exécute les tests. Le gros téléchargement n’est pas lancé automatiquement à chaque commit. Les résultats versionnés proviennent d’une exécution locale réelle et sont contrôlés par les tests de réconciliation.
