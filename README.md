<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/readme/neurolab-dark.png">
  <img alt="NeuroLab : animation du traitement d'un essai EEG, des électrodes au classifieur" src=".github/readme/neurolab-light.png">
</picture>

# NeuroLab

Reconnaître, à partir de 22 électrodes EEG, quel mouvement une personne imagine : main gauche, main droite, pieds ou langue. Le modèle apprend sur une session d'enregistrement et il est évalué sur une autre, enregistrée un autre jour.

**[Voir les résultats et les visualisations](https://badreddine05.github.io/projets/neurolab/)** · [Portfolio](https://badreddine05.github.io/)

## Le projet

Quand on imagine bouger une main, le rythme mu (autour de 10 Hz) faiblit au-dessus du cortex moteur de l'hémisphère opposé. NeuroLab cherche ces traces dans le jeu public BCI Competition IV 2a et compare deux méthodes classiques d'imagerie motrice à une référence.

Le projet est né d'un travail d'équipe en master. Cette version le reprend avec un protocole plus strict : les sessions d'apprentissage (T) et de test (E) sont séparées, le prétraitement n'utilise jamais d'information du test, et chaque score est reproductible à partir des fichiers originaux.

## Résultats

Précision équilibrée moyenne sur la session de test des neuf participants (2 592 essais d'apprentissage, 2 592 essais de test) :

| Méthode | Précision équilibrée | Étendue entre participants | κ de Cohen |
| --- | ---: | ---: | ---: |
| Référence (classe majoritaire) | 25,0 % | 25,0 à 25,0 % | 0,00 |
| Puissance spectrale + LDA | 54,1 % | 30,9 à 67,7 % | 0,39 |
| CSP + LDA | 58,1 % | 34,0 à 77,1 % | 0,44 |

CSP + LDA fait mieux que la puissance spectrale pour sept participants sur neuf. L'étendue est le minimum et le maximum observés entre participants ; ce n'est pas un intervalle de confiance. Les valeurs exactes, les matrices de confusion et le détail par participant sont dans `web/data/benchmark.json`.

## Lancer l'évaluation

Il faut Python 3.13. Le téléchargement des 18 fichiers originaux représente environ 780 Mo ; leurs empreintes SHA-256 sont vérifiées.

```sh
python -m pip install -e ".[test]"
bci-lab --download
python -m pytest
```

`bci-lab` accepte aussi `--subjects 1 3 8` pour ne traiter que certains participants, `--raw-dir` pour indiquer où sont les fichiers et `--output` pour choisir le rapport produit. Sans `--download`, il ne télécharge rien.

## Protocole

- Jeu BNCI 2014-001 (BCI Competition IV 2a) : 9 participants, 22 électrodes EEG à 250 Hz, 4 classes, 288 essais par session.
- Fenêtre analysée de 2 à 6 secondes après le début de l'essai, filtrée entre 8 et 30 Hz (Butterworth d'ordre 4, phase nulle, essai par essai).
- Les canaux EOG ne sont pas utilisés. Tous les essais étiquetés sont gardés, y compris ceux que le fournisseur signale comme contenant des artefacts.
- CSP en un-contre-tous, deux filtres par classe, covariance régularisée. Réglages fixés à l'avance : aucune recherche d'hyperparamètres ni sélection de modèle sur la session de test.

## Organisation du dépôt

| Chemin | Rôle |
| --- | --- |
| `src/bci_lab/` | Lecture des données, caractéristiques, évaluation et ligne de commande |
| `tests/` | Tests scientifiques : séparation des sessions, absence de fuite, rapport |
| `data/sources.json` | URL, taille et empreinte de chaque fichier original |
| `web/data/benchmark.json` | Rapport complet : protocole, scores, matrices de confusion, qualité, provenance |
| `projetBCI.ipynb`, `projet_IAS.pdf` | Notebook et rapport de la première version du projet |

Les scores de la première version, obtenus avec un autre protocole, ne sont pas comparables à ceux du tableau ci-dessus.

## Limites

- L'évaluation porte sur une nouvelle session d'une personne déjà vue. Elle ne dit rien d'une personne inconnue du modèle.
- Le système distingue quatre mouvements imaginés en laboratoire. Il ne lit pas la pensée, et aucune validité clinique n'est revendiquée.
- Les signaux montrés dans les visualisations du portfolio sont synthétiques et signalés comme tels.

## Données, licences et crédits

Données : BNCI Horizon 2020, [jeu 001-2014](https://bnci-horizon-2020.eu/database/data-sets), sous licence CC BY-ND 4.0. Le dépôt ne republie aucun enregistrement EEG, modifié ou non : les fichiers sont téléchargés chez le fournisseur et restent dans `data/raw/`, ignoré par Git. Référence : Tangermann, M. et al. (2012). Review of the BCI Competition IV. *Frontiers in Neuroscience*, 6, 55. [doi:10.3389/fnins.2012.00055](https://doi.org/10.3389/fnins.2012.00055).

Équipe d'origine : James Camilleri, Badreddine Channoufi, Adam Sekkat et Victor Robert-Lambrecht. Reprise et réévaluation par [Badreddine Channoufi](https://badreddine05.github.io/), avec l'aide d'outils d'IA.

## In English

NeuroLab classifies four imagined movements (left hand, right hand, feet, tongue) from 22-channel EEG in BCI Competition IV 2a. Models are trained on one recording session and tested on another, recorded on a different day. Mean balanced accuracy over nine participants: 25.0 % for the majority baseline, 54.1 % for band power + LDA, 58.1 % for CSP + LDA.
