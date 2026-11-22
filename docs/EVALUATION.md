# Évaluation CBIR et FRE

## Objectif

Mesurer le classement initial et son évolution après plusieurs itérations de Feature Relevance Estimation sur GHIM-10K. Les métriques sont calculées pour un ensemble de requêtes tirées avec une graine reproductible.

## Protocole intégré

`backend.services.evaluation` sélectionne des images requêtes dans l’index et utilise leur catégorie comme vérité de référence hors ligne. Une image est comptée pertinente si elle a la même étiquette de catégorie que la requête. La requête est exclue de ses propres candidats.

Par défaut, le feedback simulé examine exactement `top_k` résultats, comme ceux visibles dans l’interface. Il marque jusqu’à cinq images de la même catégorie comme pertinentes; FRE ne s’applique que si au moins deux images pertinentes sont disponibles. Les étiquettes du corpus ne sont **pas** utilisées pendant les recherches réelles.

### Métriques

- **Precision@K** = nombre d’images pertinentes dans les K premières / K.
- **Recall@K** = nombre d’images pertinentes dans les K premières / nombre total d’images pertinentes de la catégorie dans le corpus (hors requête elle-même).

La commande imprime un rapport JSON comprenant les paramètres du protocole, le résultat initial, chaque itération, le nombre d’itérations appliquées ou ignorées et, avec plusieurs graines, la moyenne et l’écart-type entre tirages.

## Reproduire l’évaluation

Après création de `instance/features.npz` :

```powershell
.\.venv\Scripts\python.exe -m backend.services.evaluation --queries 100 --top-k 10 --iterations 3 --seeds 42 43 44 45 46
```

Exemple avec une seule graine :

```bash
python -m backend.services.evaluation --queries 100 --top-k 10 --iterations 3 --seed 42
```

Options utiles : `--feedback-count`, `--minimum-relevant`, `--epsilon`, `--feedback-pool` et `--index`. Par défaut, `feedback_pool=top_k`. Une fenêtre plus grande que `top_k` donne accès à des candidats invisibles dans l’interface et simule un oracle; le rapport JSON le signale avec `feedback_window_matches_interface: false`.

## Résultat multi-graines documenté

Une exécution documentée utilise cinq tirages de 100 requêtes (graines 42 à 46), `K=10`, une fenêtre de feedback de 10 résultats, jusqu’à cinq retours positifs par itération et trois itérations :

| Classement | Precision@10, moyenne ± écart-type | Recall@10, moyenne ± écart-type |
|---|---:|---:|
| Initial | 0,3470 ± 0,0198 | 0,00695 ± 0,00040 |
| FRE — itération 1 | 0,4996 ± 0,0368 | 0,01001 ± 0,00074 |
| FRE — itération 2 | 0,5228 ± 0,0382 | 0,01048 ± 0,00077 |
| FRE — itération 3 | 0,5256 ± 0,0393 | 0,01053 ± 0,00079 |

Selon la graine, FRE a été appliqué à 61–77 requêtes sur 100; les autres n’avaient pas deux positifs parmi les dix résultats visibles. Une simulation avec `feedback_pool=50` atteignait Precision@10 de 0,6036 à la première itération, mais elle simule un oracle et **n’est pas** le résultat principal.

Ces chiffres sont un état d’évaluation du projet, dépendant du corpus, de l’index, du code et des paramètres. Ils ne sont pas une garantie que chaque recherche s’améliore, ne mesurent pas des jugements d’utilisateurs réels et ne sont pas directement comparables aux résultats publiés dans l’article. Reconstruire l’index ou modifier les descripteurs nécessite de relancer l’évaluation.

## Interprétation et limites

Les catégories du corpus sont un proxy grossier de pertinence visuelle. Elles ne permettent pas d’affirmer que deux images de la même catégorie sont visuellement proches selon un utilisateur. Le protocole actuel simule des retours positifs seulement; les retours négatifs ne sont pas exploités par la formule FRE. Pour une évaluation utilisateur, définir des tâches et recueillir des jugements humains en conservant le même K, puis rapporter les paramètres et le nombre de participants.
