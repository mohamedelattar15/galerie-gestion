# Plan et implémentation — Projet CBIR | Groupe G13

> **Avancement :** l'extraction des descripteurs, la normalisation, la recherche CBIR/FRE, l'authentification, la galerie SQLite, les transformations et la persistance des sessions de recherche sont implémentées et testées. Une interface web HTML/CSS/JavaScript couvre les principaux parcours, y compris les graphiques des descripteurs et le feedback FRE. L'index GHIM-10K complet (10 000 images, 329 dimensions) a été généré localement et une première évaluation hors ligne multi-graines a été exécutée. La validation par de vrais utilisateurs reste à conduire. Le dataset et l'index sont exclus du dépôt.

## 1. Présentation du projet

Ce projet consiste à développer une application web de gestion et de recherche d'images basée sur leur contenu visuel (*Content-Based Image Retrieval — CBIR*).

L'application permet aux utilisateurs de gérer une collection d'images, d'extraire leurs caractéristiques visuelles et de rechercher des images similaires à partir d'une image requête.

La particularité du travail réalisé par le **groupe G13** est l'intégration de la méthode :

**Feature Relevance Estimation (FRE)**

Cette méthode utilise les retours de l'utilisateur pour estimer l'importance des différentes caractéristiques visuelles et améliorer progressivement les résultats de recherche.

### Objectifs

- Développer une application web de gestion d'images.
- Extraire les caractéristiques de couleur et de texture.
- Mettre en place un moteur de recherche CBIR.
- Implémenter la méthode FRE.
- Intégrer les fonctionnalités dans une API REST.
- Évaluer l'amélioration des résultats après rétroaction.

---

## 2. Architecture générale

Nous proposons une architecture en couches (*Layered Architecture*) avec une séparation entre l'interface utilisateur, la logique métier, les services de traitement d'images et les données.

L'application est organisée autour de trois couches principales.

### 2.1. Couche présentation — Frontend

Cette couche représente l'interface avec laquelle l'utilisateur interagit.

**Technologies proposées : HTML, CSS et JavaScript**  
React.js reste une option si l'équipe souhaite une interface plus riche et maîtrise cette technologie.

Responsabilités :

- Authentification et gestion des utilisateurs.
- Affichage de la galerie d'images.
- Importation et téléchargement des images.
- Suppression d'images.
- Organisation des images par catégories.
- Création de catégories et sous-catégories.
- Application des transformations : recadrage (*crop*), redimensionnement (*resize*), rotation par multiples de 90° et retournement horizontal ou vertical.
- Visualisation des descripteurs visuels sur la fiche de chaque image.
- Recherche simple d'images similaires.
- Sélection des images pertinentes et non pertinentes.
- Affichage des résultats après rétroaction FRE.

Le frontend communique avec le backend à travers des requêtes HTTP utilisant le format JSON.

### 2.2. Couche métier — Backend et API REST

Cette couche contient la logique principale de l'application.

**Technologies :**

- Python.
- Flask.
- Flask-RESTful.

Elle est responsable de :

- La gestion des images.
- La gestion des catégories.
- L'extraction des caractéristiques visuelles.
- La normalisation des descripteurs.
- Le calcul des distances de similarité.
- L'exécution de la recherche CBIR.
- L'implémentation de Feature Relevance Estimation.
- La gestion des itérations de rétroaction.

Le backend expose les fonctionnalités à travers une API REST.

### 2.3. Couche données — Stockage

Cette couche assure la conservation des informations et des fichiers nécessaires au fonctionnement de l'application.

**Technologies proposées :**

- SQLite : stockage structuré proposé pour le prototype.
- PostgreSQL : option pour un déploiement ou des besoins de concurrence.
- Système de fichiers : stockage des images.
- Fichiers ou tables dédiés : stockage des descripteurs numériques.

Les données à conserver comprennent :

- Les comptes utilisateurs.
- Les images et leurs métadonnées.
- Les catégories et sous-catégories.
- Les descripteurs extraits.
- Les informations de rétroaction.
- Les paramètres et poids FRE associés aux sessions de recherche.

---

## 3. Schéma de l'architecture

```text
                  UTILISATEUR
                       |
                       v
              APPLICATION WEB
            HTML / CSS / JavaScript
              (React facultatif)
                       |
                 HTTP / JSON
                       |
                       v
             BACKEND — FLASK
              Flask-RESTful
                       |
          +------------+-------------+
          |            |             |
          v            v             v
     Gestion       Extraction     Moteur de
    des images    des features       CBIR
          |            |             |
          |            v             |
          |       Descripteurs       |
          |      couleur/texture     |
          |                          |
          |                          v
          |                    Moteur FRE
          |                  - Feedback
          |                  - Calcul des poids
          |                  - Mise à jour requête
          |                  - Distance pondérée
          |                          |
          +------------+-------------+
                       |
                       v
                COUCHE DONNÉES
                       |
          +------------+-------------+
          |            |             |
          v            v             v
      SQLite       Images        Features
                  stockées      sauvegardées
```

---

## 4. Architecture interne du Backend

Pour faciliter le développement et la maintenance, le backend est divisé en modules indépendants.

### 4.1. Module de gestion des images

Ce module prend en charge les opérations sur les images :

- Importation d'une ou plusieurs images.
- Téléchargement.
- Suppression.
- Gestion des catégories.
- Création d'une nouvelle image dérivée par recadrage ou redimensionnement, sans écraser l'originale.
- Création d'une nouvelle image dérivée par rotation par multiples de 90° ou retournement horizontal/vertical.

### 4.2. Module d'extraction des caractéristiques

Ce module extrait les descripteurs visuels nécessaires à la recherche.

**Caractéristiques de couleur :**

- Histogrammes de couleurs.
- Moments de couleur.
- Couleurs dominantes.

**Caractéristiques de texture :**

- GLCM : Contrast, Correlation, Energy, Homogeneity.
- LBP : histogramme des motifs binaires locaux.

Les histogrammes de couleur et l'histogramme LBP sont normalisés pour que la somme de leurs bins soit égale à 1. Les autres composantes numériques sont standardisées avec la moyenne et l'écart-type calculés sur la base indexée. Les mêmes paramètres sont appliqués à la requête et aux images retournées en feedback; ils ne sont pas recalculés séparément pour chaque image.

Les vecteurs normalisés sont concaténés dans un ordre fixe. La représentation des couleurs dominantes doit garder une taille et un ordre cohérents d'une image à l'autre.

Les descripteurs sont présentés de façon lisible sur la fiche de chaque image : histogrammes de couleur et LBP sous forme de graphiques, et moments de couleur et propriétés GLCM sous forme de valeurs numériques.

### 4.3. Module CBIR

Ce module réalise la recherche classique d'images similaires.

Fonctionnement :

1. Recevoir l'image requête.
2. Récupérer ou extraire son vecteur de caractéristiques.
3. Comparer ce vecteur avec ceux de la base.
4. Calculer les distances.
5. Trier les images par distance croissante.
6. Retourner les résultats les plus proches.

### 4.4. Module FRE

Ce module représente la partie principale du travail du groupe G13.

Il est responsable de l'amélioration de la recherche grâce aux retours de pertinence de l'utilisateur.

Ses responsabilités :

- Recevoir les images pertinentes sélectionnées.
- Calculer les statistiques des caractéristiques pertinentes.
- Estimer les poids des caractéristiques.
- Mettre à jour le vecteur de requête.
- Effectuer une recherche avec distance pondérée.
- Gérer les itérations successives.

### 4.5. Module API REST

Ce module expose les fonctionnalités du backend à travers des endpoints HTTP.

Il reçoit les requêtes du frontend, appelle les services correspondants et retourne les résultats au format JSON.

---

## 5. Architecture détaillée de Feature Relevance Estimation

### 5.1. Principe

La méthode FRE repose sur le fait que les caractéristiques visuelles ne contribuent pas toutes de la même manière à une recherche donnée.

À partir des images pertinentes sélectionnées par l'utilisateur, le système estime l'importance de chaque dimension du vecteur de caractéristiques.

Les caractéristiques les plus cohérentes parmi les images pertinentes obtiennent un poids plus important.

### 5.2. Déroulement du processus

**Étape 1 — Recherche initiale**

L'utilisateur sélectionne une image requête.

Le système extrait son vecteur de caractéristiques et effectue une première recherche avec des poids uniformes. Si la requête provient de la base, elle est exclue de ses propres résultats.

**Étape 2 — Rétroaction utilisateur**

L'utilisateur classe les images retournées en deux catégories :

- Relevant : images pertinentes.
- Non-Relevant : images non pertinentes.

Les deux types de jugement peuvent être conservés dans la session. Cependant, la formule FRE retenue ci-dessous utilise uniquement les images pertinentes. Les images non pertinentes ne sont pas utilisées dans cette formule.

**Étape 3 — Calcul des poids**

À l'itération \(k\), \(R_k\) désigne les images marquées pertinentes pendant cette itération. Pour chaque dimension \(i\) du vecteur normalisé, le système calcule l'écart-type des valeurs de cette dimension dans \(R_k\) :

\[
\sigma_{rel,i}^{k}=Std(\{x_i : x \in R_k\})
\]

Il utilise ensuite la formule de pondération de l'équation (4) et du tableau comparatif de l'article :

\[
w_i^k=\frac{1}{\epsilon+\sigma_{rel,i}^{k}}
\]

Avec :

\[
\epsilon=0.0001
\]

Dans cette implémentation, l'écart-type de population est utilisé pour que le calcul soit déterministe. Le seuil de deux images pertinentes minimum est un garde-fou du projet, et non une exigence formulée par l'article.

**Étape 4 — Mise à jour du vecteur de requête**

Le nouveau vecteur de requête est calculé à partir de la moyenne des vecteurs pertinents de l'itération courante :

\[
Q_{k+1}=\frac{1}{|R_k|}\sum_{X\in R_k}X
\]

**Étape 5 — Recherche avec distance quadratique pondérée**

Le système applique l'équation (3) de l'article entre le nouveau vecteur de requête et le vecteur \(Y\) de chaque image candidate :

\[
D_w(Q_{k+1},Y)=
\frac{\sum_{i=1}^{d}w_i^k(q_i^{k+1}-y_i)^2}
{\sum_{i=1}^{d}w_i^k}
\]

Il s'agit d'une distance euclidienne quadratique pondérée, sans racine carrée, conformément à la formule retenue dans le projet. Les images sont classées par distance croissante. Multiplier tous les poids par une constante commune ne change pas cette distance normalisée; plafonner des poids individuellement, en revanche, modifierait la méthode et ne sera pas activé par défaut.

**Étape 6 — Nouvelle itération**

L'utilisateur juge les nouveaux résultats. À chaque itération, les poids et le vecteur requête sont recalculés à partir des images pertinentes sélectionnées à cette itération, et non à partir d'un cumul des retours précédents. Cette règle rend explicite l'interprétation de \(R_k\) adoptée dans le projet.

### 5.3. Cas particuliers

- **Aucune image pertinente :** ne pas calculer de nouveaux poids ni modifier la requête; conserver les résultats précédents et inviter l'utilisateur à sélectionner au moins une image pertinente.
- **Une seule image pertinente :** demander au moins deux images pertinentes avant d'appliquer FRE. Avec une seule image, la dispersion n'est pas informative et l'écart-type est nul.
- **Poids élevés :** \(\epsilon\) protège contre une division par zéro. Aucun plafonnement individuel n'est appliqué par défaut; une variante avec plafonnement devra être clairement signalée et évaluée séparément.
- **Descripteur constant dans l'index :** éviter une division par zéro lors de la standardisation en utilisant une échelle de remplacement documentée, par exemple 1; cette dimension devient alors constante après normalisation.

### 5.4. Schéma du processus FRE

```text
       IMAGE REQUÊTE
             |
             v
     EXTRACTION FEATURES
             |
             v
      RECHERCHE CBIR
             |
             v
      RÉSULTATS INITIAUX
             |
             v
      FEEDBACK UTILISATEUR
             |
       +-----+------+
       |            |
       v            v
   RELEVANT     NON-RELEVANT
       |
       v
 CALCUL DES STATISTIQUES
   (images pertinentes)
       |
       v
 ESTIMATION DES POIDS FRE
       |
       v
 MISE À JOUR DE LA REQUÊTE
       |
       v
 DISTANCE QUADRATIQUE PONDÉRÉE
       |
       v
 NOUVEAUX RÉSULTATS
       |
       v
 NOUVELLE ITÉRATION
```

**Remarque :** Dans la formule FRE présentée ci-dessus, les poids sont calculés à partir de la dispersion des images pertinentes. Le texte de la section FRE décrit aussi une évaluation individuelle des caractéristiques et le comptage des images pertinentes retrouvées; cette description ne concorde pas entièrement avec l'équation (4). Le projet suit l'équation (4) et le tableau comparatif. Cette formule ne doit pas être confondue avec celle de Re-weighting Type-1.

---

## 6. Technologies et bibliothèques

| Technologie | Rôle dans le projet |
|---|---|
| HTML, CSS, JavaScript | Interface du prototype |
| React.js | Choix facultatif pour une interface plus riche |
| Python | Logique métier et algorithmes |
| Flask | Serveur backend |
| Flask-RESTful | API REST |
| Pillow ou OpenCV | Lecture et transformations des images; choisir les fonctions nécessaires |
| NumPy | Manipulation des vecteurs et calculs |
| scikit-image | Extraction GLCM et LBP |
| scikit-learn | Facultatif, par exemple pour le clustering des couleurs dominantes |
| Matplotlib | Facultatif, pour les visualisations d'analyse |
| SQLite | Stockage structuré proposé pour le prototype |
| PostgreSQL | Choix facultatif pour un déploiement ou des besoins de concurrence |

Le prototype ne nécessite pas obligatoirement React ou PostgreSQL. Éviter d'ajouter deux bibliothèques de traitement d'images si une seule suffit aux fonctions retenues.

---

## 7. Organisation du projet

Structure actuelle du code :

```text
galerie-gestion/
├── backend/
│   ├── app.py             # API Flask-RESTful et routes de recherche
│   ├── auth.py            # Inscription, connexion et sessions utilisateur
│   ├── database.py        # Schéma et accès SQLite
│   ├── features.py        # Extraction couleur, GLCM et LBP
│   ├── fre.py             # Poids FRE et distance pondérée
│   ├── gallery.py         # Catégories, galerie et transformations
│   ├── image_io.py        # Validation et stockage des images
│   ├── index.py           # Pré-calcul et chargement de l'index
│   ├── normalization.py   # Normalisation ajustée sur la base
│   ├── retrieval.py       # Classement et sessions de recherche
│   ├── static/            # Interface CSS et JavaScript
│   └── templates/         # Page de l'application
├── tests/
│   ├── test_api.py
│   ├── test_features.py
│   └── test_fre.py
├── requirements.txt
├── requirements-dev.txt
├── README.md
└── README_IMPLEMENTATION.md
```

Le dossier `GHIM-10K/` est une donnée locale ignorée par Git et ne doit pas être remis. L'index généré est stocké dans `instance/`, également ignoré. Les comptes, catégories, métadonnées de la galerie et sessions de recherche sont persistés dans SQLite; les fichiers images sont conservés dans le stockage local. Les sessions sont associées à une empreinte de l'index et ne peuvent pas être réutilisées si celui-ci change.

---

## 8. API REST : endpoints proposés

Les endpoints suivants permettent de structurer les échanges entre frontend et backend.

| Méthode | Endpoint | Fonction | État |
|---|---|---|---|
| GET | `/health` | Vérifier l'API et l'index | Implémenté |
| POST | `/api/features/extract` | Extraire les caractéristiques d'une image ou d'un lot | Implémenté |
| POST | `/api/search` | Effectuer une recherche simple | Implémenté |
| POST | `/api/search/feedback` | Effectuer une recherche avec feedback FRE | Implémenté |
| POST | `/api/auth/register`, `/api/auth/login` | Créer un compte et se connecter | Implémenté |
| POST | `/api/auth/logout`, GET `/api/auth/me` | Fermer la session et consulter le compte | Implémenté |
| GET, POST | `/api/categories` | Lister et créer des catégories | Implémenté |
| GET, POST | `/api/images` | Lister et importer des images | Implémenté |
| GET | `/api/images/<id>/file` | Afficher ou télécharger une image personnelle | Implémenté |
| GET | `/api/images/<id>/descriptors` | Calculer les descripteurs d'une image de la galerie | Implémenté |
| DELETE | `/api/images/<id>` | Supprimer une image | Implémenté |
| POST | `/api/images/<id>/transform` | Créer une image transformée | Implémenté |
| GET | `/api/indexed-images/<id>/file` | Afficher une image de l'index de recherche | Implémenté |
| DELETE | `/api/categories/<id>` | Supprimer une catégorie vide | Implémenté |

`POST /api/features/extract` accepte soit un fichier image, soit plusieurs fichiers image dans une même requête multipart (`image` ou `images`). La réponse contient un résultat par image et indique les erreurs éventuelles sans empêcher le traitement des autres fichiers valides. L'interface affiche les histogrammes HSV et LBP ainsi que les moments de couleur et les propriétés GLCM. Les descripteurs des images personnelles sont calculés à la demande; ils ne sont pas stockés en base.

### Exemple : recherche simple

```json
{
  "query_image_id": 15,
  "top_k": 10
}
```

### Exemple : recherche avec rétroaction

```json
{
  "session_id": "example-session-id",
  "query_image_id": 15,
  "relevant_ids": [21, 35, 48],
  "non_relevant_ids": [18, 27],
  "top_k": 10
}
```

Les identifiants sont des exemples destinés à illustrer le format des requêtes. Le serveur conserve l'état de la session (vecteur requête, poids et numéro d'itération); le numéro d'itération ne doit pas être accepté comme une valeur faisant autorité depuis le client.

---

## 9. Organisation du développement

Le développement doit suivre un ordre permettant de valider progressivement chaque partie.

### Phase 1 — Préparation (terminée)

- Étudier le cahier des charges.
- Comprendre le papier scientifique.
- Préparer l'environnement de développement.
- Télécharger et examiner GHIM-10K.
- Définir la structure du projet.

### Phase 2 — Extraction des caractéristiques (terminée)

- Implémenter les histogrammes de couleurs.
- Calculer les moments de couleur.
- Identifier les couleurs dominantes.
- Extraire les propriétés GLCM.
- Calculer les histogrammes LBP.
- Permettre l'extraction via l'API pour une image seule ou un lot d'images.
- Normaliser les histogrammes par somme et standardiser les autres composantes avec des paramètres calculés sur l'index.
- Réutiliser les mêmes paramètres de normalisation pour les requêtes et les images de feedback.
- Enregistrer les vecteurs.
- Pré-calculer les descripteurs du dataset et stocker leur version ainsi que les paramètres de normalisation.
- Afficher les histogrammes de couleur et LBP, ainsi que les valeurs des moments de couleur et propriétés GLCM.

### Phase 3 — Moteur de recherche CBIR (terminée)

- Sélectionner une image requête.
- Comparer ses caractéristiques avec la base.
- Calculer les distances.
- Trier les résultats.
- Afficher les images similaires.

### Phase 4 — Implémentation FRE (G13) (terminée)

- Collecter les retours utilisateur.
- Utiliser les images pertinentes de l'itération courante; ne pas utiliser directement les votes négatifs dans la formule FRE.
- Exiger deux images pertinentes au minimum comme garde-fou du projet.
- Calculer les écarts-types par dimension et appliquer l'équation (4).
- Mettre à jour le vecteur de requête avec la moyenne des vecteurs pertinents de l'itération courante.
- Implémenter l'équation (3) comme distance euclidienne quadratique pondérée.
- Relancer la recherche.
- Gérer les itérations.

### Phase 5 — Développement de l'API (implémentée)

- Configurer Flask et Flask-RESTful.
- Créer les endpoints.
- Intégrer les modules de traitement.
- Tester les réponses JSON.

### Phase 6 — Développement frontend (première version implémentée)

- Créer les pages de l'application.
- Développer la galerie.
- Ajouter les fonctionnalités de gestion d'images.
- Intégrer la recherche simple.
- Ajouter l'interface de rétroaction.
- Afficher les résultats FRE.

### Phase 7 — Tests et évaluation (tests et script d'évaluation implémentés)

- Vérifier l'extraction des descripteurs.
- Tester la recherche classique.
- Tester les poids FRE.
- Tester les cas sans retour positif, avec un seul retour positif et avec plusieurs retours positifs.
- Tester plusieurs itérations.
- Comparer les résultats avant feedback et après chaque itération, avec une valeur de \(N\) fixe.
- Calculer la précision@N et le rappel sur plusieurs requêtes, puis rapporter les moyennes.
- Exécuter `python -m backend.evaluation` pour comparer la recherche initiale et plusieurs itérations FRE.

---

## 10. Évaluation

L'évaluation permet de mesurer l'effet de la méthode FRE sur les résultats de recherche.

### Précision

\[
Precision=\frac{TP}{TP+FP}
\]

### Rappel

\[
Recall=\frac{TP}{TP+FN}
\]

Où :

- TP : images pertinentes retrouvées.
- FP : images non pertinentes retrouvées.
- FN : images pertinentes non retrouvées.

Pour l'évaluation hors ligne uniquement, une image GHIM-10K est considérée pertinente si elle appartient à la même catégorie que l'image requête. Ces étiquettes servent à mesurer les résultats ou à simuler un utilisateur; elles ne doivent pas être fournies à l'algorithme de recherche lors de son fonctionnement normal. Si la requête appartient à la base, elle doit être exclue des résultats évalués.

Les expériences doivent comparer, sur les mêmes requêtes et avec le même \(N\) :

1. La recherche CBIR classique.
2. La recherche après une première itération FRE.
3. La recherche après plusieurs itérations FRE.

L'outil `python -m backend.evaluation` exécute ce protocole et émet un rapport JSON avec Precision@N, Recall@N et le nombre de feedbacks appliqués ou ignorés à chaque itération. Il échantillonne les requêtes avec une graine reproductible et exclut la requête de son propre classement. Pour simuler le feedback hors ligne, il sélectionne les exemples positifs de même catégorie parmi les premiers résultats; les étiquettes ne sont jamais fournies au moteur CBIR/FRE en fonctionnement normal. Les cas avec moins de deux positifs disponibles sont comptabilisés et ne déclenchent pas de mise à jour FRE.

Les résultats doivent être mesurés sur GHIM-10K et interprétés après exécution du protocole. Présenter ses paramètres (requêtes, catégories, \(N\), sélection des retours et nombre d'itérations) avec toute performance annoncée. Les chiffres de l'article sur son propre dataset ne doivent pas être présentés comme des résultats GHIM-10K.

### Résultat de la première évaluation multi-graines

L'évaluation a utilisé cinq tirages reproductibles de 100 requêtes chacun (graines 42 à 46), \(N=10\), une fenêtre de feedback de 50 résultats et jusqu'à cinq positifs simulés par itération. Le feedback FRE a été appliqué à 90–98 requêtes sur 100 selon le tirage; les autres requêtes n'avaient pas deux positifs disponibles. Le tableau indique la moyenne et l'écart-type de population des métriques moyennes des cinq tirages.

| Classement | Précision@10 (moyenne ± écart-type) | Rappel@10 (moyenne ± écart-type) |
|---|---:|---:|
| CBIR initial | 0,3336 ± 0,0206 | 0,00669 ± 0,00041 |
| Après FRE — itération 1 | 0,6036 ± 0,0286 | 0,01210 ± 0,00057 |
| Après FRE — itération 2 | 0,6208 ± 0,0296 | 0,01244 ± 0,00059 |
| Après FRE — itération 3 | 0,6208 ± 0,0278 | 0,01244 ± 0,00056 |

Ces chiffres décrivent uniquement cette simulation oracle fondée sur les catégories GHIM-10K; ils ne mesurent pas le comportement de vrais utilisateurs et ne constituent pas une comparaison directe avec les résultats de l'article.

---

## 11. Livrables

### Rapport scientifique

Le rapport doit présenter :

- La problématique.
- Le fonctionnement du CBIR.
- Les descripteurs visuels.
- L'étude du papier scientifique.
- La méthode FRE.
- L'architecture logicielle.
- Les détails de l'implémentation.
- Les résultats expérimentaux.
- La conclusion.

### Code source

Le dossier final doit contenir :

- Le frontend.
- Le backend Flask.
- Les modules d'extraction.
- Le moteur CBIR.
- Le moteur FRE.
- Les tests.
- Les fichiers de configuration.
- Les dépendances.
- La documentation.

Le dataset et les sous-dossiers générés volumineux doivent être exclus du dossier de remise.

---

## 12. Conclusion

L'architecture proposée permet de séparer les responsabilités de l'application et de faciliter son développement.

Le frontend assure l'interaction avec l'utilisateur, l'API Flask centralise la logique métier, et les modules de traitement réalisent l'extraction des caractéristiques et la recherche d'images.

Pour le groupe G13, le composant central est le moteur **Feature Relevance Estimation**. Il exploite les images pertinentes sélectionnées par l'utilisateur pour estimer les poids des caractéristiques, mettre à jour la requête et améliorer le classement des images.

Cette architecture permet ainsi d'intégrer la méthode scientifique FRE dans une application web complète de recherche d'images par le contenu visuel.

---

## Références

- Renuka Devi SM, *Reweighing Strategies for Relevance Feedback in CBIR*, IJARCCE, Volume 5, Issue 11, November 2016.
- Dataset : [GHIM-10K — Kaggle](https://www.kaggle.com/datasets/mcpython/ghim-10k)