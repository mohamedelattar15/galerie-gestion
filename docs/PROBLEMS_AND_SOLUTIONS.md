# Problèmes traités, solutions et limites

## Problématique CBIR

La recherche par fichier ou mot-clé ne trouve pas les ressemblances visuelles lorsque l’utilisateur ne connaît pas le nom de l’image. Le CBIR représente chaque image par des descripteurs de couleur et de texture, calcule une distance avec la requête et retourne les candidats les plus proches.

La distance visuelle ne correspond pas toujours au jugement de l’utilisateur : deux images partageant une couleur ou une texture peuvent représenter des scènes différentes. Ce décalage est le **fossé sémantique**. Le retour de pertinence FRE permet à l’utilisateur d’influencer une session en désignant les images pertinentes.

## Difficultés et réponses dans le code

| Problème | Réponse implémentée | Limite à garder à l’esprit |
|---|---|---|
| Une grande zone uniforme, souvent le fond, domine l’histogramme. | Modes `variance` et `adaptive`; le mode global reste disponible comme référence. | Le masque adaptatif suppose que les bordures représentent un fond relativement homogène. Il peut être inadapté à une scène sans fond distinct. |
| Les familles de caractéristiques ont des échelles différentes. | Racine carrée de Hellinger pour histogrammes; standardisation des autres dimensions à partir de l’index. | Toute modification des descripteurs ou de la normalisation nécessite une reconstruction de l’index. |
| Une couleur très vive mais petite n’apparaît pas dans les couleurs dominantes. | Calcul et affichage auxiliaire d’une couleur d’accent saturée. | Cette couleur d’accent est seulement informative; elle n’influence pas la distance CBIR ni FRE. |
| Le premier classement ne sait pas ce que l’utilisateur juge pertinent. | Feedback FRE itératif avec adaptation du vecteur requête et des poids. | Au moins deux positives sont nécessaires; la formule actuelle n’exploite pas les votes négatifs. |
| Plusieurs utilisateurs peuvent tenter d’accéder aux ressources d’un autre compte. | Sessions authentifiées, filtrage des ressources par propriétaire et validations des identifiants. | L’application est un prototype local; elle n’inclut pas toute l’infrastructure de sécurité et d’exploitation d’un service public. |
| Une image peut devenir orpheline si son enregistrement échoue. | Les routes suppriment les fichiers en cas d’échec de persistance; la suppression utilise un fichier temporaire de transition. | Une sauvegarde régulière du dossier `instance/` reste nécessaire pour les données personnelles. |

## Points non résolus / travaux futurs

- Les caractéristiques sont des descripteurs classiques et ne comprennent pas de représentation sémantique issue d’un réseau profond.
- La segmentation par couleur du contour est heuristique; une segmentation erronée peut manquer l’objet ou garder du fond. Le mode global permet une comparaison de référence.
- Les catégories GHIM-10K fournissent un signal grossier : deux images de la même catégorie ne sont pas forcément similaires pour l’utilisateur.
- L’évaluation est simulée avec ces catégories. Elle ne remplace pas des expériences avec des participants et une tâche clairement définie.
- Les votes négatifs ne sont pas intégrés à la formule FRE actuelle.
- Le moteur parcourt les vecteurs de l’index par calcul NumPy exhaustif. Pour un corpus nettement plus grand, il faudrait mesurer les performances et étudier un index vectoriel dédié.
- Le mode choisi à l’indexation doit correspondre au mode descripteur de la requête; les variantes sont donc pré-calculées et stockées séparément.

## Comment vérifier une amélioration

Une modification de la représentation doit être évaluée avec les mêmes requêtes, le même `top_k`, le même protocole de feedback et plusieurs graines. Ne comparez pas une recherche où l’utilisateur juge uniquement les dix résultats affichés à une simulation qui utilise cinquante candidats sans expliquer la différence. Consultez [EVALUATION.md](EVALUATION.md).
