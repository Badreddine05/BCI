# Revue du notebook historique

Le notebook et le rapport d’origine sont conservés sans modification. Ils rendent compte d’un travail académique de James Camilleri, Badreddine Channoufi, Adam Sekkat et Victor Robert–Lambrecht. Leur présence conserve les étapes et limites de l’étude ; leurs sorties ne sont pas les résultats du nouveau protocole.

Les numéros ci-dessous sont les indices des cellules JSON, à partir de zéro, dans `projetBCI.ipynb` au commit `8e76227`.

| Cellule | Problème constaté | Traitement dans la refonte |
| --- | --- | --- |
| 26 | L’addition NumPy entre T et E additionne les signaux élément par élément ; elle ne concatène pas les sessions. | Deux objets `Epochs` distincts, jamais additionnés ; T apprend, E évalue. |
| 41, 46, 50… | Des fragments d’enregistrements sont répartis aléatoirement, sans protocole entre jours explicite. | Découpage immuable selon la session de capture. Les résultats ne prétendent pas identifier une personne inconnue. |
| 57 | La QDA personnalisée renvoie l’indice de la probabilité maximale au lieu du label d’origine. Les densités peuvent sous-déborder. | `RegularizedQDA` conserve `classes_`, calcule en log, régularise la covariance et résout par Cholesky. |
| 66 | La boucle sur les électrodes lit toujours le canal 0. | Les 22 EEG sont sélectionnés explicitement ; les canaux EOG restent exclus du modèle. |
| 81 | `X[:, 0:x]` utilise une variable d’une boucle précédente au lieu de la taille courante. | Extraction de fenêtres validée avec bornes et dimensions fixes. |
| 107–114 | La PCA est ajustée sur tout X avant le découpage apprentissage/test. | Aucune transformation apprise hors de la pipeline d’apprentissage. Le nouveau benchmark n’utilise pas de PCA. |
| 128–150 | La normalisation du CNN utilise un maximum global avant découpage ; des expériences emploient le test comme validation pendant l’entraînement. | Séparation stricte entre jours ; aucun CNN non réévalué n’est annoncé dans les nouveaux résultats. |
| 165–171 | L’optimisation de reconstruction ne vérifie pas son statut ; les tirages sont non fixés. | `reconstruct_sparse_dct` valide les entrées, le statut du solveur et la contrainte de mesure. Le test synthétique a une graine fixe. |
| 184 | La taille préallouée des matrices de corrélation ne correspond pas au nombre de fenêtres, laissant des matrices nulles artificielles. | Allocation depuis les fenêtres complètes réellement présentes, dernière fenêtre incluse, corrélation indéfinie conservée comme indisponible. |
| 190 | Une chaîne complète est passée comme nom de programme à `Popen`, sans arguments séparés. | Le pipeline d’évaluation n’a pas besoin de FFmpeg ; aucune génération vidéo cassée n’est conservée dans son exécution. |

La refonte n’a pas pour objectif de gonfler les anciens scores. Le protocole est plus exigeant, avec une comparaison fixe et une provenance vérifiable. Les explorations de corrélation ne démontrent pas un lien causal entre régions cérébrales.
