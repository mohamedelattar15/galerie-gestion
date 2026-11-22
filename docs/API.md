# API HTTP

Base locale : `http://127.0.0.1:5000`. Les routes protégées utilisent le cookie de session Flask créé à l’inscription ou à la connexion. Les erreurs JSON ont la forme `{"error": "…"}`. Les téléversements sont multipart/form-data; les actions applicatives utilisent généralement JSON.

## Santé, authentification et recherche

| Méthode | Route | Accès | Fonction |
|---|---|---|---|
| `GET` | `/health` | Public | État de l’application, index chargé, nombre d’images et modes disponibles. |
| `POST` | `/api/auth/register` | Public | Créer un compte et ouvrir une session. Nom de 3–32 caractères autorisés; mot de passe de 12–256 caractères. |
| `POST` | `/api/auth/login` | Public | Ouvrir une session. |
| `POST` | `/api/auth/logout` | Session | Fermer la session. |
| `GET` | `/api/auth/me` | Session | Lire l’identité de l’utilisateur connecté. |
| `POST` | `/api/features/extract` | Session | Calculer les descripteurs de `image` ou d’un lot `images` (32 maximum). |
| `POST` | `/api/search` | Session | Recherche à partir de `query`, `gallery_image_id` ou `query_image_id`; accepte `top_k` et `descriptor_mode`. |
| `POST` | `/api/search/feedback` | Session | Appliquer une itération avec `session_id`, `relevant_ids`, `non_relevant_ids` et éventuellement `top_k` / `descriptor_mode`. Au moins deux IDs pertinents sont requis. |

Pour la recherche par téléversement, utilisez `multipart/form-data`. Pour les votes FRE, envoyez du JSON. Le `session_id` doit appartenir à l’utilisateur connecté et les votes doivent référencer les résultats de l’itération en cours. Les identifiants `query_image_id` correspondent aux positions dans l’index; `gallery_image_id` correspond à une image personnelle appartenant à l’utilisateur.

## Galerie et catégories

| Méthode | Route | Fonction |
|---|---|---|
| `GET` | `/api/categories` | Lister les catégories de l’utilisateur. |
| `POST` | `/api/categories` | Créer une catégorie; JSON `name` et optionnellement `parent_id`. |
| `DELETE` | `/api/categories/<category_id>` | Supprimer une catégorie vide appartenant à l’utilisateur. |
| `GET` | `/api/images` | Lister la galerie; paramètres `limit`, `offset`, `category_id`, `sort`, `q`. |
| `POST` | `/api/images` | Importer un ou plusieurs fichiers `images` (32 maximum), optionnellement `category_id`. |
| `GET` | `/api/images/<image_id>` | Lire les métadonnées d’une image personnelle. |
| `GET` | `/api/images/<image_id>/file` | Afficher le fichier; ajouter `?download=1` pour forcer le téléchargement. |
| `GET` | `/api/images/<image_id>/descriptors` | Calculer les descripteurs de l’image et renvoyer leur détail. |
| `GET` | `/api/images/<image_id>/analysis` | Mesures de séparabilité et URLs de carte/masque disponibles. |
| `GET` | `/api/images/<image_id>/mask` | Renvoyer le masque objet en PNG si le masque est calculable. |
| `GET` | `/api/images/<image_id>/background-map` | Renvoyer la carte de différence avec le fond en PNG. |
| `DELETE` | `/api/images/<image_id>` | Supprimer l’image; les images dérivées doivent d’abord être supprimées. |
| `POST` | `/api/images/<image_id>/transform/preview` | Prévisualiser en PNG une transformation décrite en JSON. |
| `POST` | `/api/images/<image_id>/transform` | Créer une copie transformée en PNG, en conservant la source. |
| `GET` | `/api/indexed-images/<image_id>/file` | Afficher une image du corpus indexé. |

Valeurs de `sort` : `created_desc`, `created_asc`, `name_asc`. La liste est paginée (limite maximale 100 par requête). Les opérations de transformation acceptées sont `crop`, `resize`, `rotate`, `flip`, `brightness`, `contrast`, `saturation`, `sharpness`, `grayscale`, `sepia`, `blur` et `autocontrast`.

## Opérations groupées

Ces routes attendent du JSON contenant les identifiants d’images qui appartiennent à l’utilisateur :

| Méthode | Route | Fonction |
|---|---|---|
| `POST` | `/api/images/batch-delete` | Supprimer une sélection d’images. |
| `POST` | `/api/images/batch-move` | Déplacer la sélection avec `category_id` (ou `null`). |
| `POST` | `/api/images/batch-download` | Télécharger la sélection dans une archive ZIP. |

## Exemple de recherche

```bash
curl -b cookies.txt -c cookies.txt -F "query=@photo.jpg" -F "top_k=10" -F "descriptor_mode=global" http://127.0.0.1:5000/api/search
```

L’authentification doit d’abord être faite sur `/api/auth/login` ou `/api/auth/register` en conservant le cookie avec `-c` / `-b`. La réponse de recherche contient `session_id`, le mode utilisé, les informations du corpus et les résultats avec `id`, `path`, `category` et `distance`.
