# Architecture

```text
src/bci_lab/
  data.py        identité de source, téléchargement, empreintes, extraction EEG
  features.py    filtrage hors ligne, puissance spectrale, CSP ajusté
  evaluation.py protocole T -> E, modèles, métriques et agrégation
  analysis.py   QDA stable, corrélations glissantes, reconstruction DCT
  cli.py        paramètres explicites et erreurs de ligne de commande
tests/          invariants scientifiques, fixtures et contrôle du rapport
data/sources.json             manifeste des 18 sources originales
web/data/benchmark.json       contrat de restitution pour le frontend
```

Un import ne télécharge aucune donnée et n’entraîne aucun modèle. Le réseau n’est utilisé que sur demande `--download`. Les fonctions reçoivent leurs entrées explicitement et ne dépendent pas de l’ordre d’exécution d’un notebook.

La frontière avec le frontend est un JSON statique, sans backend public ni clé d’accès. Les matrices, labels, protocoles et agrégats sont transportés ensemble, pour éviter qu’une visualisation combine des résultats incompatibles. Les jeux EEG originaux, fichiers temporaires et environnements virtuels sont exclus du dépôt.

Les tests couvrent les erreurs constatées dans le notebook et les invariants de la chaîne : origine des indices MATLAB, exclusion EOG, bandes fréquentielles, conservation des effectifs, labels arbitraires, fenêtre complète finale, séparation des sessions et paramètres d’apprentissage immuables pendant la prédiction.
