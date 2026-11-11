# Contrat frontend — BCI / NeuroLab

La réalisation du frontend est séparée du pipeline scientifique. Ce contrat décrit les données validées, leur provenance et leurs limites pour l’équipe interface.

## Données disponibles

`web/data/benchmark.json` est généré par `python -m bci_lab.cli --download`. Le benchmark complet a été exécuté sur les neuf participants : 2 592 essais d’apprentissage et 2 592 essais d’évaluation, sessions séparées. Les tests scientifiques passent. Moyennes de précision équilibrée : référence 25 %, puissance spectrale + LDA 54,09 %, CSP + LDA 58,06 %. Reprendre les valeurs exactes du JSON, pas les arrondis de cette note.

Schéma version 1 :

- `subjects`: participants effectivement évalués, identifiants 1 à 9 du jeu public.
- `protocol`: sessions T pour apprendre, E pour tester ; 22 canaux EEG, quatre classes, 250 Hz, intervalle [2, 6) secondes, filtre hors ligne 8–30 Hz.
- `records`: une ligne par participant et modèle (`baseline`, `bandpower`, `csp`). Champs : `subject`, `model`, `name`, `train_trials`, `test_trials`, `accuracy`, `balanced_accuracy`, `kappa`, `confusion`.
- `summary`: moyennes arithmétiques entre participants ; `subject_min`/`subject_max` représentent l’étendue observée, **pas un intervalle de confiance**. Matrice de confusion cumulée.
- `confusion`: lignes = vraie classe, colonnes = classe prédite ; ordre fixe `left_hand`, `right_hand`, `feet`, `tongue`.
- `quality`: nombre d’essais, de runs, d’essais marqués avec artefacts et effectifs par classe, par session.
- `sources`: URL officielle, taille et SHA-256 de chaque fichier original.
- `runtime`, `generated_at`, `data_license`, `source_page`, `publication`: provenance.

## Présentation recommandée

Comparaison des trois modèles, filtres participant/modèle, matrice de confusion et rappel par classe, tableau des participants, export CSV/JSON et protocole détaillé. Pourcentages = valeur numérique × 100. Le kappa n’est pas un pourcentage. La précision équilibrée moyenne est une moyenne de participants ; ne pas la recalculer à partir de la matrice cumulée sans le préciser.

Les données ont une licence **CC BY-ND 4.0**. Le dépôt ne republie aucun enregistrement EEG modifié. Les résultats statistiques calculés sont publiés ; les signaux bruts restent dans `data/raw/`, ignoré par Git, téléchargeables chez le fournisseur.

Un éventuel laboratoire de signal interactif doit employer des **signaux synthétiques explicitement étiquetés**, ou des données que le visiteur charge localement. Ne pas présenter un signal simulé comme un EEG enregistré. Le projet évalue une nouvelle session d’une personne connue ; il ne prouve pas une généralisation à de nouvelles personnes, une lecture de pensée ou une validité clinique.

## Historique et crédits

Le notebook `projetBCI.ipynb` et le rapport `projet_IAS.pdf` sont conservés. Auteurs originaux : James Camilleri, Badreddine Channoufi, Adam Sekkat, Victor Robert–Lambrecht. Le nouveau pipeline corrige les mélanges de sessions, les fuites de prétraitement et plusieurs erreurs d’indexation du notebook historique. Les anciens scores ne doivent pas être mélangés avec le nouveau benchmark.
