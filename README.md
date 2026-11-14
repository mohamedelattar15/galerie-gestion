# Gestion et recherche d'images par le contenu — G13

Projet universitaire de gestion d'une galerie d'images et de recherche CBIR (*Content-Based Image Retrieval*), encadré par **M'hamed AIT KBIR**.

Le groupe **G13** travaille sur **Feature Relevance Estimation (FRE)** : une méthode de retour de pertinence qui utilise les images marquées pertinentes pour ajuster les poids des caractéristiques et améliorer le classement des résultats.

> **Avancement :** le backend d'extraction, indexation, recherche CBIR/FRE, authentification et gestion de galerie est implémenté. Une interface web HTML/CSS/JavaScript permet la connexion, la gestion des images et catégories, les transformations, la visualisation des descripteurs et la recherche avec feedback. L'index GHIM-10K de 10 000 images est généré localement; les sessions de recherche sont conservées dans SQLite. Une première évaluation hors ligne multi-graines est réalisée; des essais avec de vrais utilisateurs restent à conduire.

## Objectifs du projet

- Gérer une galerie d'images après authentification : import, téléchargement, suppression, catégories et transformations (recadrage, redimensionnement, rotation et retournement).
- Extraire les descripteurs d'une image ou d'un lot d'images, puis les visualiser.
- Fournir une API REST avec Python, Flask et Flask-RESTful.
- Rechercher les images similaires à une image requête.
- Améliorer les résultats par des itérations de feedback FRE.
- Évaluer la recherche initiale et les résultats après feedback.

## Descripteurs demandés

| Famille | Descripteurs |
|---|---|
| Couleur | Histogrammes, moments de couleur et couleurs dominantes |
| Texture — GLCM | Contraste, corrélation, énergie et homogénéité |
| Texture — LBP | Histogramme des motifs binaires locaux |

## Documentation

- [Rapport de projet G13 — version de travail](RAPPORT_G13_CBIR_FRE.docx)
- [Plan d'architecture et d'implémentation](README_IMPLEMENTATION.md) — architecture proposée, formule FRE, API, étapes de réalisation, cas limites et protocole d'évaluation.
- [Explication détaillée du projet](explication.md)
- Article de référence : Renuka Devi SM, [DOI 10.17148/IJARCCE.2016.511118](https://doi.org/10.17148/IJARCCE.2016.511118). La copie PDF de travail n'est pas incluse dans l'archive de livraison.

Le plan distingue les exigences du projet des choix techniques proposés. La formule et les choix d'implémentation de FRE doivent être décrits conformément à l'article et à la méthode attribuée à G13.

## Dataset

Le projet utilise [GHIM-10K sur Kaggle](https://www.kaggle.com/datasets/mcpython/ghim-10k). La copie locale comprend 20 catégories de 500 images, soit 10 000 images. Certains noms de dossiers contiennent des espaces, par exemple `dragon fly` et `sea shores`.

Les catégories peuvent servir de vérité de référence pour une évaluation hors ligne. Elles ne remplacent pas les jugements de l'utilisateur pendant une recherche réelle. Le dataset ne doit pas être inclus dans le dossier final remis, conformément au sujet. L'index généré (`instance/features.npz`) est ignoré par Git et doit être reconstruit localement.

## Technologies

**Exigences du projet :** Python, Flask et Flask-RESTful pour l'API REST.  
**Choix de prototype proposés :** HTML/CSS/JavaScript, SQLite, système de fichiers et descripteurs pré-calculés. React et PostgreSQL restent des options, pas des exigences.

## Installation, indexation et lancement

Depuis la racine du dépôt, avec Python 3.12 ou plus récent :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Pré-calculer les descripteurs du dataset :

```powershell
.\.venv\Scripts\python.exe -m backend.index --dataset GHIM-10K --output instance\features.npz
```

Lancer l'API en mode développement :

```powershell
.\.venv\Scripts\python.exe -m backend.app
```

L'API est alors accessible sur `http://127.0.0.1:5000`. `GET /health` indique si l'index est chargé. Sans index, l'extraction fonctionne, mais les recherches répondent avec une erreur explicite.

Exécuter les tests :

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Évaluer CBIR et plusieurs itérations FRE hors ligne :

```powershell
.\.venv\Scripts\python.exe -m backend.evaluation --queries 100 --top-k 10 --feedback-pool 50 --feedback-count 5 --iterations 3 --seeds 42 43 44 45 46
```

Le rapport JSON compare Precision@K et Recall@K sur les mêmes requêtes. Les catégories simulent les jugements positifs uniquement pour cette évaluation hors ligne; elles ne sont pas utilisées par la recherche normale.

## Interface et routes principales

Ouvrir `http://127.0.0.1:5000` après le lancement du serveur. L'interface couvre l'inscription et la connexion, les catégories, l'import et la suppression d'images, les transformations, l'affichage des descripteurs et la recherche avec feedback.

- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` — authentification.
- `GET|POST /api/categories` — liste et création des catégories; `DELETE /api/categories/<id>` — suppression d'une catégorie vide.
- `GET|POST /api/images` — galerie et import; `GET /api/images/<id>/file` — aperçu, avec `?download=1` pour télécharger; `GET /api/images/<id>/descriptors` — calcul des descripteurs; `POST /api/images/<id>/transform` — création d'une copie transformée; `DELETE /api/images/<id>` — suppression.
- `POST /api/features/extract` — multipart avec `image` ou plusieurs fichiers `images`.
- `POST /api/search` — multipart avec `query` et `top_k`, ou avec `query_image_id`.
- `POST /api/search/feedback` — JSON contenant `session_id`, au moins deux `relevant_ids`, et éventuellement des `non_relevant_ids`.
- `GET /api/indexed-images/<id>/file` — aperçu d'une image de l'index de recherche.

Les retours négatifs sont reçus mais ne sont pas utilisés par la formule FRE de G13. Les sessions de recherche, leur vecteur courant, leurs poids, les résultats et le numéro d'itération sont conservés dans SQLite et restent liés à leur propriétaire. Si l'index change, les anciennes sessions sont refusées et une nouvelle recherche est nécessaire.

## Livrables attendus

- Rapport `.doc`, `.docx` ou `.pdf`.
- Code source de l'application et de l'API.
- Fichiers nécessaires à l'installation et à l'exécution.
- Documentation et tests.
- Dossier final sans le dataset ni les données générées automatiquement.

## Références

- Renuka Devi SM, « Reweighing Strategies for Relevance Feedback in CBIR », *International Journal of Advanced Research in Computer and Communication Engineering*, vol. 5, no. 11, novembre 2016, DOI : [10.17148/IJARCCE.2016.511118](https://doi.org/10.17148/IJARCCE.2016.511118).
- [Dataset GHIM-10K — Kaggle](https://www.kaggle.com/datasets/mcpython/ghim-10k)
- [Documentation Flask](https://flask.palletsprojects.com/)
- [Documentation Flask-RESTful](https://flask-restful.readthedocs.io/)
