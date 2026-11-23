# Détection du sujet et traitement du fond

Ce guide décrit la méthode effectivement utilisée dans le projet, ses limites sur les images GHIM-10K et les améliorations possibles. Il est important de distinguer **détection d’objet** et **estimation du premier plan** : le code actuel ne reconnaît ni les classes d’objets ni leurs boîtes. Il produit un masque heuristique à partir des couleurs de bordure et de quelques mesures de séparabilité.

## Pourquoi le fond perturbe la recherche ?

Les descripteurs globaux résument tous les pixels. Si un fond uniforme occupe la majeure partie d’une photo, ses couleurs peuvent peser plus que celles du sujet. Deux photos de sujets différents prises devant un fond proche peuvent alors être classées ensemble; à l’inverse, le même sujet sur des fonds différents peut être éloigné.

Le problème est particulièrement visible sur les sujets petits, les fleurs photographiées avec un arrière-plan flou, les objets sur un ciel ou une surface uniforme et les photos dont le fond représente plus de la moitié de l’image.

## Méthode utilisée actuellement

Le code pertinent se trouve dans `backend/domain/segmentation/` et `backend/services/analysis.py`.

### 1. Préparation de l’image

Pour l’analyse d’affichage et l’extraction des caractéristiques, l’image est convertie en RGB et réduite afin que son plus grand côté ne dépasse pas 256 pixels. Le tableau RGB est ramené dans l’intervalle `[0, 1]`.

### 2. Estimation de la couleur du fond

Le système prélève une bande de bordure de largeur égale à **15 % du plus petit côté**. La moyenne RGB des pixels de cette bordure sert de couleur de fond estimée.

Pour chaque pixel (p), il calcule une distance euclidienne à cette couleur moyenne (b) :

\[
d(p,b)=\|p-b\|_2
\]

Un pixel est considéré comme premier plan si cette distance dépasse la tolérance `0.18`. Le masque est donc blanc pour les pixels différents du fond estimé et noir pour ceux qui en sont proches.

### 3. Garde-fous de séparabilité

Le masque n’est jugé plausible que si la proportion marquée comme sujet est comprise entre **8 % et 95 %**. Le système calcule aussi un ratio :

\[
S=\frac{\|\mu_{bord}-\mu_{centre}\|_2}{\max(\sigma_{bord},10^{-6})}
\]

où \(\mu\) désigne une moyenne de couleur et \(\sigma_{bord}\) la dispersion moyenne des couleurs de la bordure. Si `S` dépasse **1.2** et que le masque est plausible, l’analyse recommande le mode adaptatif. Sinon, elle recommande le mode variance. Ce ratio est un indicateur heuristique; il ne constitue pas une probabilité de bonne détection.

L’interface affiche l’image originale, une carte de distance à la couleur du bord, la proportion du masque et le masque binaire lorsqu’il est jugé plausible. La carte est normalisée à partir du 95e percentile des distances afin que les écarts soient visibles.

### 4. Repli par variance spatiale

Le mode variance découpe l’image en une grille **4 × 4**. Il calcule la variance RGB dans chaque bloc et donne plus de poids aux blocs qui varient davantage. Un plancher `0.05` maintient une contribution minimale des zones uniformes; les poids sont ensuite normalisés.

Cette méthode ne dit pas « cet objet est une fleur ». Elle exploite l’hypothèse que les régions détaillées contiennent souvent davantage d’information que les zones uniformes.

## Effet sur les descripteurs dans cette implémentation

Le nom `adaptive` ne signifie pas que chaque descripteur est calculé uniquement sur le sujet. La portée actuelle est la suivante :

| Bloc de caractéristiques | Mode `global` | Mode `variance` | Mode `adaptive` si masque accepté |
|---|---|---|---|
| Histogramme HSV | Toute l’image | Pondération par variance | Toute l’image |
| Moments RGB | Toute l’image | Pondération par variance | Toute l’image |
| Couleurs dominantes | Toute l’image | Toute l’image | Toute l’image |
| GLCM | Toute l’image | Toute l’image | Toute l’image |
| LBP | Toute l’image | Toute l’image | Pixels retenus par le masque |

Si le masque adaptatif est refusé, les histogrammes HSV et moments RGB utilisent les poids du mode variance et le LBP redevient global. Cette différence est essentielle pour interpréter les résultats : le mode adaptatif actuel réduit l’effet du fond pour le LBP, mais pas pour toutes les caractéristiques couleur ou texture.

## Causes probables d’un masque incorrect

- **Le sujet touche la bordure** : la moyenne du bord contient une partie du sujet et l’estimation du fond est contaminée.
- **Le fond n’est pas uniforme** : feuillage, texture, ombres ou gradient de lumière augmentent la dispersion de la bordure.
- **Le sujet et le fond ont des couleurs proches** : une partie du sujet peut être classée comme fond.
- **Plusieurs couleurs composent le fond** : une seule moyenne RGB ne représente pas le fond.
- **Des éléments éloignés ont une couleur différente du fond** : ils sont inclus, même s’ils ne sont pas le sujet principal.
- **Le masque est dispersé** : le seuil RGB produit des pixels isolés; le code actuel ne fait pas de regroupement par connectivité ni de fermeture morphologique.
- **Le sujet occupe presque toute l’image ou est minuscule** : le garde-fou 8–95 % rend le masque indisponible, même si certaines zones sont visuellement identifiables.

La variance a aussi ses limites : les textures du fond peuvent recevoir plus de poids que le sujet et un sujet lisse peut être sous-pondéré.

## Améliorations possibles, par priorité

1. **Évaluer un échantillon représentatif** : conserver pour chaque photo l’original, le masque et le mode conseillé; annoter manuellement un sous-ensemble et mesurer précision, rappel et IoU. Cela permet d’ajuster `0.18`, `1.2`, `8 %` et `95 %` à partir de données plutôt qu’à l’œil.
2. **Améliorer le masque heuristique** : calculer la couleur de fond dans plusieurs segments de bordure, utiliser une distance perceptuelle comme CIELAB et distinguer les pixels connectés au contour des régions internes. Ajouter opérations morphologiques uniquement après inspection pour éviter de supprimer des détails fins.
3. **Appliquer le masque de manière cohérente** : calculer les histogrammes de couleur et les moments RGB sur le premier plan lorsqu’un masque fiable est accepté; décider séparément si couleurs dominantes et GLCM doivent être masculés ou conservés en global. Reconstruire tous les index concernés après changement.
4. **Proposer une correction à l’utilisateur** : permettre de marquer un masque comme bon/mauvais, d’ajuster sa tolérance ou de corriger la zone de sujet par un outil simple. Garder le mode global comme référence et solution de repli.
5. **Ajouter une segmentation entraînée si le besoin le justifie** : un modèle de premier plan (par ex. U²-Net) ou un modèle de segmentation interactif peut mieux traiter les scènes complexes. Il faut alors documenter les poids et licences, la latence, les besoins matériels, la résolution et la qualité sur le corpus; ce n’est pas inclus actuellement.

Un détecteur de classes tel que YOLO répond à une question différente (où se trouvent les objets reconnus). Il n’est pas automatiquement un meilleur extracteur de premier plan pour toutes les photos; le choix doit correspondre au besoin et être évalué.

## Protocole de comparaison conseillé

Pour mesurer une amélioration du traitement du fond :

1. Générer les index `global`, `variance` et `adaptive` à partir du même corpus.
2. Utiliser les mêmes images requêtes, les mêmes valeurs de `top_k`, les mêmes graines et le même protocole de feedback.
3. Comparer Precision@K et Recall@K avant et après FRE, ainsi que le nombre de sessions où le feedback a pu être appliqué.
4. Sur le sous-ensemble annoté, mesurer la qualité des masques indépendamment de la qualité du classement.
5. Rapporter les échecs typiques, le temps de calcul et les réglages. Une amélioration du masque ne garantit pas à elle seule une meilleure recherche.

Voir également [Méthodes CBIR et FRE](METHODS.md), [Problèmes et limites](PROBLEMS_AND_SOLUTIONS.md) et [Évaluation](EVALUATION.md).
