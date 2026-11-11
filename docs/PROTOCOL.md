# Protocole d’évaluation

Le benchmark distingue les **sessions d’enregistrement**, plutôt que de répartir au hasard des fragments issus d’une même session. Pour chaque participant, le modèle apprend sur le fichier T et est évalué une fois sur le fichier E, enregistré un autre jour. Les participants ne sont pas mélangés dans un même modèle.

## Sources et extraction

Le jeu [BNCI2014-001](https://bnci-horizon-2020.eu/database/data-sets), également connu comme BCI Competition IV 2a, contient neuf participants et quatre tâches d’imagerie motrice : main gauche, main droite, pieds et langue. Les deux sessions de chacun comprennent six runs de 48 essais. Référence : [Tangermann et al., 2012](https://doi.org/10.3389/fnins.2012.00055). Le [descriptif du fournisseur](https://bnci-horizon-2020.eu/database/data-sets/001-2014/description.pdf) détaille acquisition et événements.

Le chargeur lit les MAT originaux du serveur de TU Graz. Il convertit les débuts d’essai MATLAB, indexés à partir de 1, en indices Python. Chaque fenêtre couvre **[2, 6) secondes** depuis le début de l’essai : 1 000 échantillons à 250 Hz, fin exclusive. Le début correspond à l’apparition de la consigne. Cet intervalle est également celui du [chargeur MOABB](https://moabb.neurotechx.com/docs/generated/moabb.datasets.BNCI2014_001.html).

Les 22 canaux EEG sont conservés, en microvolts. Les trois canaux EOG sont exclus. Les enregistrements de calibration sans événement sont ignorés. Les essais marqués avec artefacts par le fournisseur restent inclus ; leur nombre est rapporté dans `quality`. Aucun rejet d’essai fondé sur la classe ou sur la performance n’est effectué. Les tailles, labels, bornes, valeurs finies et sommes de contrôle sont contrôlés.

## Transformations et modèles

Le filtrage fixe est un Butterworth d’ordre 4, entre 8 et 30 Hz, appliqué dans les deux sens **à chaque fenêtre séparément**. Il ne mélange ni sessions ni essais. Il s’agit d’un traitement hors ligne : il utilise toute la fenêtre et ne constitue pas une chaîne de décision causale en temps réel. Le traitement par fenêtre peut aussi introduire des effets de bord ; ces choix sont identiques pour les deux modèles entraînés.

Trois modèles sont comparés avec des paramètres fixés avant le benchmark :

| Modèle | Variables | Estimation |
| --- | --- | --- |
| Classe majoritaire | Prédiction constante de la classe majoritaire dans T | Référence simple ; 25 % sur les sessions équilibrées présentes |
| Puissance spectrale + LDA | Log-puissance de Welch par canal dans 8–12 Hz et 13–30 Hz, soit 44 variables | StandardScaler, puis LDA avec shrinkage automatique |
| CSP + LDA | CSP un-contre-reste, deux filtres spatiaux par classe, soit huit variables de log-variance | Covariances normalisées par trace, régularisation 0,1 ; StandardScaler et même LDA |

CSP, normalisation et classifieur sont appris **uniquement dans T**, dans une pipeline scikit-learn. La covariance CSP est estimée sur les essais d’apprentissage ; `transform` ne réapprend aucun paramètre sur E. Les valeurs de test n’interviennent pas dans le choix des variables, du nombre de composantes ou des hyperparamètres. Aucune recherche de paramètres sur E n’a été menée. La [documentation scikit-learn sur les fuites](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage) explique la séparation utilisée.

## Résultats exécutés

Les résultats complets sont dans `web/data/benchmark.json`, avec versions logicielles, protocole, 18 empreintes SHA-256, effectifs et matrices de confusion. Au total : **2 592 essais d’apprentissage et 2 592 essais d’évaluation**, pour neuf modèles individuels par méthode.

| Méthode | Précision équilibrée, moyenne entre participants | Kappa, moyenne entre participants | Étendue de précision équilibrée |
| --- | ---: | ---: | ---: |
| Classe majoritaire | 25,00 % | 0,000 | 25,00–25,00 % |
| Puissance spectrale + LDA | 54,09 % | 0,388 | 30,90–67,71 % |
| CSP + LDA | 58,06 % | 0,441 | 34,03–77,08 % |

Les moyennes donnent le même poids à chaque participant. L’étendue est le minimum–maximum observé, **pas un intervalle de confiance**. Les matrices de confusion cumulées regroupent les prédictions de neuf modèles différents. L’exactitude et la précision équilibrée coïncident ici parce que chaque session possède 72 essais par classe ; ce n’est pas une identité générale.

## Limites

- Le protocole évalue une nouvelle session d’une personne connue. Il ne mesure pas la généralisation à une personne jamais rencontrée.
- Neuf participants ne permettent pas de conclure à une performance universelle. Les écarts entre participants sont visibles et importants.
- Les signaux comportent des artefacts conservés. Aucune correction EOG, sélection de canaux ni adaptation de domaine n’est ajoutée après observation des scores.
- Les résultats ne sont pas directement comparables aux anciens scores du notebook, aux protocoles avec rejet d’artefacts, aux découpages aléatoires ou aux évaluations inter-participants.
- Ce travail est une analyse de recherche hors ligne, sans usage clinique ni dispositif de lecture de pensées.

## Distribution

Les enregistrements sont sous [CC BY-ND 4.0](https://creativecommons.org/licenses/by-nd/4.0/), concédée par l’Institute for Knowledge Discovery de TU Graz. Ils sont téléchargés depuis le fournisseur et restent dans un répertoire ignoré par Git. Le dépôt publie du code et des résultats statistiques, pas des enregistrements EEG modifiés. Toute animation de signaux synthétiques dans le frontend doit être explicitement identifiée comme telle.
