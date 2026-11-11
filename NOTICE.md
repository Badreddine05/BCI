# Origine et conditions de réutilisation

Le notebook `projetBCI.ipynb` et le rapport `projet_IAS.pdf` proviennent du projet collectif de **James Camilleri, Badreddine Channoufi, Adam Sekkat et Victor Robert–Lambrecht**. Ils sont conservés sans modification. Le nouvel avis MIT ne leur attribue pas une nouvelle licence et n’efface pas leurs auteurs.

Le code de refonte dans `src/bci_lab`, les tests et scripts de construction sont couverts par `LICENSE-new-code.txt`. Cette refonte a été réalisée avec l’assistance de Codex ; les résultats publiés proviennent d’exécutions documentées, pas de scores générés.

Les fichiers EEG **BNCI2014-001**, concédés par l’Institute for Knowledge Discovery, Graz University of Technology, sont sous [CC BY-ND 4.0](https://creativecommons.org/licenses/by-nd/4.0/). Ils restent chez leur [fournisseur](https://bnci-horizon-2020.eu/database/data-sets) et dans le cache local ignoré par Git. Référence scientifique : [Tangermann et al., 2012, Review of the BCI competition IV](https://doi.org/10.3389/fnins.2012.00055).

Les bibliothèques NumPy, SciPy et scikit-learn sont installées séparément par l’utilisateur et conservent leurs licences. Elles ne sont pas recopiées dans le dépôt. Le verrou `uv.lock` décrit leurs versions. Les résultats statistiques et les sommes de contrôle sont fournis avec leur protocole ; ils ne constituent pas une redistribution des signaux EEG modifiés.
