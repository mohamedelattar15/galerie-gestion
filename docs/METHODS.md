# Méthodes CBIR et Feature Relevance Estimation

## Problème traité

CBIR (*Content-Based Image Retrieval*) recherche des images à partir des pixels et de descripteurs numériques, sans s’appuyer sur une recherche textuelle. L’utilisateur peut toutefois juger une image « similaire » selon son intention, qui n’est pas toujours capturée par les caractéristiques visuelles : c’est le fossé sémantique.

La méthode attribuée à **G13 est Feature Relevance Estimation (FRE)**. Dans la liste des groupes du sujet, FRE concerne G1, G5, G10, G13, G14 et G16.

## Descripteurs implémentés

Le vecteur fait **329 dimensions**. L’ordre est fixé par `backend/domain/features.py` :

| Bloc | Taille | Calcul |
|---|---:|---|
| Histogramme HSV | 48 | 16 classes pour chacun des canaux H, S et V. |
| Moments RGB | 9 | Moyenne, écart-type et asymétrie pour R, V/vert et B. |
| Couleurs dominantes | 12 | Trois triplets RGB quantifiés par median-cut et trois proportions d’aire. |
| GLCM | 4 | Contraste, corrélation, énergie et homogénéité, moyennés sur quatre directions. |
| LBP | 256 | Histogramme des 256 motifs binaires construits à partir des huit voisins du pixel. |

La « couleur d’accent la plus vive » est un descripteur auxiliaire affiché dans l’interface. Elle est absente de `ImageDescriptor.vector`; elle n’entre donc ni dans la recherche simple ni dans FRE.

## Normalisation et recherche initiale

La normalisation est ajustée lors de la construction de l’index, puis réutilisée pour transformer chaque requête :

- Sur les histogrammes HSV et LBP, le système applique la racine carrée aux fréquences (embedding de Hellinger), puis la distance euclidienne. Cela évite de comparer ces distributions comme des blocs de grande amplitude brute.
- Sur les moments, couleurs dominantes et propriétés GLCM, le système applique une standardisation par moyenne et écart-type calculés sur le corpus. Les échelles nulles sont remplacées par 1.
- La recherche initiale utilise un vecteur de poids égal à 1 partout. La distance est une distance quadratique pondérée normalisée; les résultats sont classés par distance croissante.

## Formule FRE utilisée

Soit (R_k) l’ensemble des images marquées pertinentes par l’utilisateur à l’itération courante. Pour chaque dimension (i), le poids est l’inverse de la dispersion des valeurs dans ces images :

\[
w_i = \frac{1}{\varepsilon + \sigma_i(R_k)}, \qquad \varepsilon=0.0001
\]

L’écart-type est calculé comme écart-type de population (`ddof=0`). Les dimensions peu dispersées au sein des images pertinentes reçoivent un poids plus élevé. Le vecteur requête est remplacé par la moyenne des vecteurs pertinents de l’itération courante :

\[
q_{k+1}=\frac{1}{|R_k|}\sum_{x\in R_k}x
\]

La distance candidate est :

\[
D(q,x)=\frac{\sum_i w_i(q_i-x_i)^2}{\sum_i w_i}
\]

À chaque itération, les votes doivent concerner les résultats présentés à l’itération précédente. Il faut au moins deux images pertinentes. Les feedbacks négatifs sont validés et comptés par l’API, mais ne participent pas actuellement au calcul FRE.

## Modes de traitement du fond

Ils changent la façon dont certains descripteurs sont calculés, pas la formule FRE :

- **Global** : toute l’image contribue aux histogrammes et moments pondérés; c’est le mode par défaut.
- **Variance** : l’image est découpée en une grille 4×4. Les zones de variance élevée reçoivent davantage de poids; un poids plancher évite de supprimer entièrement une région.
- **Adaptatif** : une couleur de fond moyenne est estimée à partir des bordures et comparée aux pixels de l’image pour produire un masque. Le masque n’est accepté que s’il garde une proportion plausible de pixels et si le contraste centre/bord est assez distinct. Sinon, le calcul revient à la pondération par variance.

En mode variance, les poids spatiaux s’appliquent aux histogrammes HSV et aux moments RGB. En mode adaptatif, si le masque est accepté, il est appliqué au calcul LBP; les histogrammes HSV et moments RGB redeviennent globaux. Si le test adaptatif échoue, le mode variance sert de repli pour ces blocs. Les couleurs dominantes et les propriétés GLCM sont calculées sur l’image entière dans les trois modes. Cette méthode de segmentation classique n’est pas un modèle sémantique universel.

## Génération des variantes

```powershell
python -m backend.services.indexing --dataset GHIM-10K --output instance\features.npz --mode global
python -m backend.services.indexing --dataset GHIM-10K --output instance\features_variance.npz --mode variance
python -m backend.services.indexing --dataset GHIM-10K --output instance\features_adaptive.npz --mode adaptive
```

Construire un nouvel index est nécessaire après modification du code des descripteurs ou de leur normalisation. L’empreinte de l’index empêche la poursuite d’une session FRE créée avec un index différent.

## Référence

Renuka Devi SM, [“Reweighing Strategies for Relevance Feedback in CBIR”](https://doi.org/10.17148/IJARCCE.2016.511118), *IJARCCE*, vol. 5, no 11, 2016. Les équations et l’algorithme effectifs doivent être compris à partir de cet article et comparés à `backend/domain/fre.py` et `backend/services/search.py`.
