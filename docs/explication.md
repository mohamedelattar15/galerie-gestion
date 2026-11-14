# Système de Gestion et de Recherche d’Images par le Contenu (CBIR)

## Projet : Content-Based Image Retrieval avec Feature Relevance Estimation (FRE)

> **Nature de ce document :** il explique la méthode et décrit l'implémentation telle qu'elle existe dans le dépôt. Les paramètres de FRE sont définis dans `backend/domain/fre_config.py`, l'organisation du code est détaillée au §9.3 et les résultats expérimentaux au §14.3.

---

## 1. Présentation du projet

L’objectif de ce projet est de développer une application web permettant de gérer une collection d’images et d’effectuer une recherche d’images similaires à partir de leur contenu visuel.

Contrairement à une recherche classique basée sur le nom du fichier, les mots-clés ou les métadonnées, le système CBIR (*Content-Based Image Retrieval*) analyse directement les caractéristiques visuelles des images.

L’application doit permettre à un utilisateur de :

- Créer un compte et s’authentifier.
- Importer une ou plusieurs images.
- Télécharger et supprimer des images.
- Organiser les images dans des catégories hiérarchiques.
- Appliquer des transformations aux images, comme le recadrage et le redimensionnement.
- Extraire et visualiser les descripteurs visuels des images.
- Rechercher des images similaires à une image requête.
- Améliorer les résultats grâce à la rétroaction de pertinence (*Relevance Feedback*).

### Méthode attribuée au groupe

**Feature Relevance Estimation (FRE)**

Groupes concernés : G1, G5, G10, G13 et G14.

Cette méthode consiste à estimer l'importance des différentes caractéristiques visuelles pour améliorer la recherche d'images similaires.

---

## 2. Comprendre le CBIR

### 2.1. Définition

Le CBIR (*Content-Based Image Retrieval*) est une technique permettant de rechercher des images dans une base de données en analysant leur contenu visuel.

Chaque image est représentée par un ensemble de caractéristiques numériques appelées descripteurs.

Le système compare ensuite les descripteurs de l'image requête avec ceux des images de la base de données afin de retrouver les images les plus similaires.

### 2.2. Fonctionnement général

Le processus de recherche suit les étapes suivantes :

1. L'utilisateur sélectionne une image requête.
2. Le système extrait ses caractéristiques visuelles.
3. Les caractéristiques sont représentées sous forme de vecteurs numériques.
4. Le système compare le vecteur de la requête avec les vecteurs des images de la base.
5. Les distances de similarité sont calculées.
6. Les images les plus proches sont classées et affichées.

### 2.3. Les principales catégories de caractéristiques

Dans ce projet, les caractéristiques visuelles demandées concernent principalement la couleur et la texture.

#### A. Descripteurs de couleur

La couleur permet de représenter la distribution des couleurs dans une image.

Les descripteurs à implémenter sont :

**1. Histogramme de couleurs**

Un histogramme représente la distribution des intensités ou des couleurs dans une image.

Il permet de comparer deux images en étudiant leurs distributions de couleurs.

**2. Moments de couleur**

Les moments statistiques décrivent la distribution des couleurs.

Les principaux moments sont :

- Moyenne : représente la valeur moyenne des couleurs.
- Écart-type : mesure la dispersion des valeurs.
- Asymétrie (Skewness) : mesure l'asymétrie de la distribution.

**3. Couleurs dominantes**

Cette méthode consiste à identifier les couleurs les plus représentatives d'une image.

Elle peut être réalisée à l'aide d'un algorithme de clustering comme K-Means.

#### B. Descripteurs de texture

La texture permet de représenter les motifs et les variations locales présents dans une image.

Les descripteurs demandés sont :

**1. GLCM (Gray-Level Co-occurrence Matrix)**

La GLCM est une matrice qui décrit la fréquence de cooccurrence de deux niveaux de gris séparés par une distance et une orientation données.

Elle permet de calculer plusieurs propriétés :

- Contrast : mesure les variations locales d'intensité.
- Correlation : mesure la dépendance entre les niveaux de gris.
- Energy : mesure l'uniformité de la distribution.
- Homogeneity : mesure la proximité des éléments de la matrice par rapport à sa diagonale.

**2. LBP (Local Binary Patterns)**

Le LBP est un descripteur permettant de caractériser les textures locales.

Il compare chaque pixel avec ses voisins et génère un motif binaire.

Les motifs obtenus sont ensuite représentés sous forme d'un histogramme de fréquences.

---

## 3. Comprendre la recherche d'images similaires

### 3.1. Vecteur de caractéristiques

Chaque image est représentée par un vecteur contenant ses descripteurs.

Exemple simplifié :

```text
Image A :
[
  histogramme_couleur,
  moments_couleur,
  couleurs_dominantes,
  GLCM,
  LBP
]
```

Les valeurs numériques extraites constituent la représentation de l'image dans l'espace des caractéristiques.

Il est nécessaire de normaliser les caractéristiques afin d'éviter qu'un descripteur ayant des valeurs numériques plus grandes domine artificiellement les autres.

### 3.2. Calcul de similarité

Pour comparer deux images, le système calcule une distance entre leurs vecteurs de caractéristiques.

Le papier présente notamment la distance euclidienne normalisée :

\[
Dist(X,Y)=
\sqrt{\frac{\sum_{i=1}^{d}(x_i-y_i)^2}{d}}
\]

Avec :

- \(X\) : vecteur de l'image requête.
- \(Y\) : vecteur de l'image candidate.
- \(x_i\) et \(y_i\) : valeurs des caractéristiques.
- \(d\) : dimension du vecteur.

Une distance faible indique une plus grande proximité entre les deux images.

Le système trie les résultats par distance croissante et affiche les images les plus proches.

Dans l'implémentation, la recherche initiale utilise des poids uniformes : la formule pondérée du §6.3 se réduit alors à une moyenne des écarts au carré, sans racine carrée, ce qui conserve le même ordre de classement.

---

## 4. Comprendre le papier scientifique

### 4.1. Référence

**Titre :** Reweighing Strategies for Relevance Feedback in CBIR

**Auteur :** Renuka Devi SM

**Publication :** International Journal of Advanced Research in Computer and Communication Engineering (IJARCCE), Volume 5, Issue 11, novembre 2016.

Ce papier étudie différentes stratégies de rétroaction de pertinence pour améliorer les systèmes de recherche d'images basés sur leur contenu.

### 4.2. Le problème : Semantic Gap

Le papier explique que les caractéristiques visuelles de bas niveau ne représentent pas toujours correctement la signification que l'utilisateur attribue à une image.

Par exemple, deux images peuvent avoir des couleurs similaires sans représenter le même objet.

Ce problème est appelé **Semantic Gap** (fossé sémantique).

Pour réduire ce problème, le papier présente la technique de Relevance Feedback.

### 4.3. Relevance Feedback

La rétroaction de pertinence est un mécanisme permettant à l'utilisateur d'indiquer si les images retournées par le système correspondent réellement à sa recherche.

Le fonctionnement est le suivant :

1. L'utilisateur choisit une image requête.
2. Le système retourne une première liste d'images similaires.
3. L'utilisateur indique les images pertinentes et non pertinentes.
4. Le système exploite ces informations pour améliorer la recherche.
5. Une nouvelle liste de résultats est générée.
6. Le processus peut être répété jusqu'à obtenir des résultats satisfaisants.

**Exemple :**

L'utilisateur recherche une image représentant un chat.

Le système retourne 10 images :

- 6 images sont pertinentes.
- 4 images ne sont pas pertinentes.

L'utilisateur sélectionne les images pertinentes et non pertinentes. Le système utilise ces informations pour ajuster sa recherche.

### 4.4. Short-Term Learning et Long-Term Learning

Le papier distingue deux types d'apprentissage.

**Short-Term Learning (STL)**

L'apprentissage se déroule pendant une seule session de recherche.

Le système utilise les retours de l'utilisateur pour améliorer progressivement les résultats de la requête actuelle.

Chaque nouvelle recherche peut repartir de zéro.

**Long-Term Learning (LTL)**

Le système exploite les informations issues des interactions précédentes afin de bénéficier de l'expérience accumulée sur plusieurs recherches ou utilisateurs.

Pour notre projet, la priorité est de mettre en place le Short-Term Learning, car la méthode FRE doit exploiter les retours de pertinence pendant une session de recherche.

---

## 5. Les différentes méthodes présentées dans le papier

Le papier présente plusieurs stratégies de rétroaction de pertinence.

Il est important de distinguer ces méthodes, car elles ne réalisent pas toutes la même opération.

### 5.1. Query Vector Modification (QVM)

Cette méthode consiste à modifier le vecteur de la requête à partir des images pertinentes et non pertinentes.

Le but est de rapprocher le vecteur de requête des images pertinentes et de l'éloigner des images non pertinentes.

Une formulation classique de cette stratégie est :

\[
Q_{new} =
Q_{old}
+\alpha \frac{1}{|R|}\sum_{X\in R}X
-\beta \frac{1}{|N|}\sum_{X\in N}X
\]

Avec :

- \(Q_{old}\) : ancien vecteur de requête.
- \(Q_{new}\) : nouveau vecteur de requête.
- \(R\) : ensemble des images pertinentes.
- \(N\) : ensemble des images non pertinentes.
- \(\alpha\) et \(\beta\) : coefficients de mise à jour.

Cette formule est une formulation classique de QVM, et non une formule à attribuer automatiquement à toutes les variantes du papier.

### 5.2. Feature Relevance Estimation (FRE)

**C'est la méthode attribuée à notre groupe.**

La méthode FRE repose sur l'idée que toutes les caractéristiques visuelles n'ont pas la même importance pour une requête donnée.

Par exemple, pour rechercher des images de fleurs :

- La couleur peut être particulièrement importante.
- La texture peut également être utile.
- D'autres caractéristiques peuvent être moins discriminantes pour cette recherche.

L'objectif de FRE est donc d'estimer l'importance de chaque caractéristique et de lui attribuer un poids.

Ces poids permettent de modifier la distance utilisée pour comparer les images.

Le système accorde ainsi davantage d'importance aux caractéristiques qui distinguent mieux les images pertinentes.

### 5.3. Re-weighting Type-1

Cette méthode ajuste les poids des caractéristiques en comparant leur dispersion dans les images pertinentes et dans l'ensemble des images récupérées.

Elle utilise :

\[
w_i^{k+1} =
\frac{\epsilon+\sigma_{N_r,i}^{k}}
{\epsilon+\sigma_{rel,i}^{k}}
\]

Avec :

- \(\sigma_{N_r,i}^{k}\) : écart-type de la caractéristique \(i\) sur les images récupérées.
- \(\sigma_{rel,i}^{k}\) : écart-type de cette caractéristique sur les images pertinentes.
- \(\epsilon\) : petite constante permettant d'éviter une division par zéro.
- \(k\) : numéro de l'itération.

**Attention :** Re-weighting Type-1 est une méthode différente de Feature Relevance Estimation. Il ne faut pas confondre leurs formules.

### 5.4. Re-weighting Type-2

Cette stratégie utilise les images non pertinentes afin d'évaluer leur présence dans la plage de valeurs caractéristique des images pertinentes.

L'objectif est de mieux distinguer les images pertinentes des images non pertinentes.

### 5.5. Re-weighting Type-3

Cette stratégie combine les principes des méthodes Type-1 et Type-2.

Elle cherche à utiliser simultanément les informations de dispersion des images pertinentes et celles des images non pertinentes.

### 5.6. Disturbing Factor

Le papier présente également un facteur perturbateur basé sur le critère de Fisher.

Son objectif est d'aider le système à sortir de certains états sous-optimaux pendant le processus d'apprentissage.

Ces stratégies sont présentées pour comprendre le contexte scientifique du projet. Notre implémentation doit principalement se concentrer sur FRE.

---

## 6. Fonctionnement détaillé de Feature Relevance Estimation (FRE)

### 6.1. Principe

La méthode FRE estime la pertinence des différentes caractéristiques avant le calcul de similarité.

Le principe est de déterminer quelles caractéristiques permettent de retrouver les images pertinentes.

Le papier décrit notamment une approche dans laquelle chaque caractéristique est évaluée individuellement :

1. Sélectionner une caractéristique.
2. Projeter les images de la base sur cette caractéristique.
3. Effectuer une recherche en utilisant uniquement cette caractéristique.
4. Observer les images retournées.
5. Compter les images pertinentes retrouvées.
6. Estimer l'importance de cette caractéristique.

Le papier indique que le poids peut être considéré comme proportionnel au nombre d'images pertinentes retrouvées grâce à cette caractéristique.

### 6.2. Estimation des poids par écart-type

Le papier présente également une formule explicite pour calculer les poids à partir de la dispersion des caractéristiques parmi les images pertinentes :

\[
w_i =
\frac{1}{\epsilon+\sigma_{rel,i}^{k}}
\]

Avec :

- \(w_i\) : poids de la caractéristique \(i\).
- \(\epsilon=0.0001\) : constante de stabilisation.
- \(\sigma_{rel,i}^{k}\) : écart-type de la caractéristique \(i\) calculé sur les images pertinentes à l'itération \(k\).

**Interprétation :**

- Si une caractéristique varie peu entre les images pertinentes, son écart-type est faible.
- Son poids devient alors plus élevé.
- Si une caractéristique varie beaucoup, son poids diminue.

L'objectif est de donner plus d'importance aux caractéristiques qui présentent une meilleure cohérence parmi les images pertinentes.

**Point méthodologique important :**

Le papier présente deux explications complémentaires de l'estimation de pertinence : le comptage des images pertinentes retrouvées par caractéristique et la formule explicite basée sur l'inverse de l'écart-type.

Ces deux descriptions ne doivent pas être fusionnées en une formule unique. Pour une implémentation fidèle à la formule de pondération présentée dans le tableau comparatif du papier, on utilisera :

\[
w_i =
\frac{1}{0.0001+\sigma_{rel,i}^{k}}
\]

Le comptage par caractéristique peut être étudié comme une stratégie d'évaluation complémentaire.

**Application dans notre implémentation :**

- L'écart-type est calculé avec `ddof=0` (écart-type de population), pour un résultat déterministe.
- Au moins deux images pertinentes sont exigées; avec une seule, la dispersion n'est pas informative.
- Les poids ne sont pas normalisés : la distance divise déjà par leur somme.
- Une caractéristique quasi constante parmi les positives reçoit un poids très élevé; la normalisation de la distance en neutralise l'effet sur le classement. Aucun plafonnement n'est appliqué.

### 6.3. Distance euclidienne quadratique pondérée

Après le calcul des poids, le système utilise une distance pondérée :

\[
Dist(X,Y)=
\frac{
\sum_{i=1}^{d}w_i(x_i-y_i)^2
}{
\sum_{i=1}^{d}w_i
}
\]

Avec :

- \(X\) : vecteur de l'image requête.
- \(Y\) : vecteur de l'image candidate.
- \(w_i\) : poids de la caractéristique \(i\).
- \(d\) : nombre de caractéristiques.

Cette formule est celle présentée dans le papier pour FRE.

Une distance faible signifie que les deux images sont proches en tenant compte de l'importance attribuée à chaque caractéristique.

Il faut respecter cette formule lors de la reproduction de la méthode. Ne pas ajouter automatiquement une racine carrée, car le papier présente ici une distance pondérée sous forme de somme normalisée des distances au carré.

**Application dans notre implémentation :** la fonction `weighted_squared_euclidean` de `backend/domain/fre.py` applique exactement cette formule, sans racine carrée, et rejette les poids négatifs ou de somme nulle.

### 6.4. Mise à jour du vecteur de requête

Le tableau comparatif du papier associe également FRE à une mise à jour du vecteur de requête par la moyenne des images pertinentes :

\[
Q_{new} =
\frac{1}{|R|}
\sum_{X\in R}X
\]

Avec :

- \(Q_{new}\) : nouveau vecteur de requête.
- \(R\) : ensemble des images pertinentes.
- \(|R|\) : nombre d'images pertinentes.

Cette mise à jour permet de représenter la zone de l'espace des caractéristiques correspondant aux images jugées pertinentes.

---

## 7. Algorithme FRE à implémenter

Voici le déroulement réellement implémenté dans le projet. Les paramètres de la méthode (epsilon, nombre minimal d'images pertinentes, nombre de résultats) sont centralisés dans `backend/domain/fre_config.py`, source unique de vérité partagée par la formule, l'API et l'évaluation.

### Étape 1 : Préparation de la base d'images

- Charger les images du dataset GHIM-10K.
- Vérifier les formats et les fichiers.
- Extraire les caractéristiques visuelles de chaque image.
- Normaliser les descripteurs.
- Enregistrer les vecteurs dans un index NumPy compressé (`instance/features.npz`), chargé au démarrage de l'API.

### Étape 2 : Recherche initiale

- L'utilisateur sélectionne une image requête (fichier envoyé ou identifiant d'une image indexée).
- Le système extrait son vecteur de caractéristiques et le normalise avec les paramètres de l'index.
- Le système compare ce vecteur avec les vecteurs de la base, avec des poids uniformes.
- Les images les plus proches sont affichées; si la requête appartient à l'index, elle est exclue de ses propres résultats.
- Une session de recherche est créée et conservée en base avec son empreinte d'index.

Cette première recherche constitue la référence avant rétroaction.

### Étape 3 : Collecte de la rétroaction

L'utilisateur indique les images :

- Pertinentes (Relevant).
- Non pertinentes (Non-Relevant).

Les deux listes sont validées : pas de doublons, pas d'image à la fois pertinente et non pertinente, et uniquement des images issues des résultats de l'itération courante.

**Les images non pertinentes sont conservées mais ne participent pas au calcul des poids.** L'équation (4) utilisée par G13 ne dépend que des images pertinentes; les négatives servent aux stratégies de re-weighting comparées dans l'article, pas à FRE.

### Étape 4 : Estimation des poids

À partir des images pertinentes, calculer l'écart-type de chaque caractéristique.

**Condition d'application :** au moins deux images pertinentes. Avec une seule image, l'écart-type est nul et n'informe pas sur la dispersion; l'API répond alors avec une erreur 422 et la recherche précédente est conservée.

Pour chaque dimension \(i\) :

\[
\sigma_{rel,i}^{k} =
Std(R_i)
\]

Puis :

\[
w_i =
\frac{1}{0.0001+\sigma_{rel,i}^{k}}
\]

L'écart-type de population (`ddof=0`) est utilisé pour rendre le calcul déterministe. Les poids ne sont **pas** normalisés : la distance de l'étape 6 divise déjà par leur somme, ce qui rend toute normalisation préalable sans effet sur le classement.

### Étape 5 : Mise à jour de la requête

Calculer le nouveau vecteur de requête à partir de la moyenne des vecteurs des images pertinentes :

\[
Q_{new} =
Mean(R)
\]

### Étape 6 : Nouvelle recherche

- Utiliser le nouveau vecteur de requête.
- Appliquer les poids FRE.
- Calculer les distances pondérées.
- Trier les images par distance croissante.
- Afficher les nouveaux résultats.

### Étape 7 : Répétition

L'utilisateur peut donner une nouvelle rétroaction.

À chaque itération, les poids et le vecteur de requête sont recalculés **uniquement à partir des images pertinentes de cette itération**, sans cumul des retours précédents.

Le processus se répète jusqu'à ce que l'utilisateur soit satisfait des résultats.

### Pseudo-code

```text
ALGORITHM Feature_Relevance_Estimation

INPUT:
    Database D
    Query image Q
    Number of results K
    epsilon = 0.0001
    minimum_relevant = 2

OUTPUT:
    Ranked images

1. Extract and normalize feature vector FQ from Q

2. Load precomputed feature vectors FI for every image I in D

3. Perform initial retrieval with uniform weights:
       Compute weighted squared distance between FQ and FI
       Sort images by ascending distance
       Display top K images
       Create a search session bound to the index fingerprint

4. Collect user feedback on the displayed results:
       R = relevant images
       N = non-relevant images (validated, not used by FRE)

5. If |R| < minimum_relevant:
       Keep the previous search and its weights
       Return an error asking for more relevant images
       Stop

6. Compute the new query:
       Q_new = Mean(feature vectors of R)

7. Estimate feature weights:
       For each feature dimension i:
           sigma_i = StandardDeviation(R[:, i])
           w_i = 1 / (epsilon + sigma_i)

8. Perform weighted retrieval:
       For each image I in D:
           Compute sum(w_i * (Q_new_i - FI_i)^2) / sum(w_i)

9. Sort images by ascending weighted distance

10. Display new results and store the updated session

11. Repeat from step 4 if the user wants another iteration

END
```

---

## 8. Dataset : GHIM-10K

Le projet utilise le dataset :

**GHIM-10K**

Lien : https://www.kaggle.com/datasets/mcpython/ghim-10k

Ce dataset constitue la collection d'images utilisée pour tester le fonctionnement de la recherche et évaluer les résultats.

### Travail à effectuer sur le dataset

1. Télécharger le dataset depuis Kaggle.
2. Extraire les fichiers dans le projet.
3. Examiner sa structure et ses catégories.
4. Vérifier les formats des images.
5. Préparer les images pour l'extraction des descripteurs.
6. Extraire les caractéristiques de couleur et de texture.
7. Stocker les caractéristiques extraites afin d'éviter de les recalculer à chaque recherche.

**Important :** Le dossier du dataset ne doit pas être inclus dans le dossier final du projet à remettre, conformément aux consignes.

---

## 9. Architecture technique proposée

Le projet est organisé autour de deux parties principales : l'application web et l'API de traitement d'images. Côté backend, le code est réparti en cinq couches.

### 9.1. Application Web

L'application web gère l'interaction avec l'utilisateur.

Ses responsabilités sont :

- Authentification.
- Gestion des images.
- Gestion des catégories.
- Téléchargement et suppression.
- Transformations des images.
- Affichage des descripteurs.
- Recherche d'images similaires.
- Interface de rétroaction de pertinence.

Le choix du framework frontend et du framework backend dépend de l'organisation du groupe. Pour l'implémentation actuelle, le groupe a retenu React + Vite; ce choix ne constitue pas une exigence imposée par la méthode CBIR/FRE.

### 9.2. API Python

L'API est développée avec :

- Python.
- Flask.
- Flask-RESTful.
- Pillow et NumPy pour le traitement d'images et les calculs.

Elle assure :

- L'extraction des descripteurs.
- La génération des vecteurs de caractéristiques.
- Le calcul des distances.
- L'exécution de l'algorithme FRE.
- Le retour des résultats à l'application web.

### 9.3. Organisation en couches du backend

```text
backend/
├── app.py            Fabrique Flask : configuration et enregistrement des routes
├── routes/           Couche HTTP : validation des entrées et réponses JSON
├── services/         Cas d'usage : recherche, authentification, galerie, indexation
├── domain/           Algorithme pur : descripteurs, FRE, normalisation, classement
├── database/         Connexion SQLite et repositories (SQL centralisé)
└── utils/            Utilitaires techniques : lecture et stockage des images
```

Règle de dépendance : `routes → services → domain/database`. Le domaine ne dépend ni de Flask ni de SQLite, ce qui permet de tester la formule FRE et la distance sans serveur.

Les paramètres de FRE (`epsilon`, `minimum_relevant`, `top_k`, fenêtre de feedback) sont définis dans `domain/fre_config.py`. Modifier une valeur de la méthode ne demande donc qu'une seule modification.

### 9.4. Communication entre les composants

L'application web communique avec l'API Python à travers des requêtes HTTP REST.

Exemple de fonctionnement :

```text
Utilisateur
    |
    v
Application Web
    |
    | Requête HTTP
    v
API Flask-RESTful
    |
    +---- Extraction des caractéristiques
    |
    +---- Calcul de similarité
    |
    +---- Feature Relevance Estimation
    |
    v
Résultats JSON
    |
    v
Application Web
    |
    v
Affichage des images similaires
```

---

## 10. API REST : endpoints implémentés

Les endpoints suivants sont réellement exposés par l'API.

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/health` | État de l'API et de l'index chargé |
| POST | `/api/auth/register` | Créer un compte |
| POST | `/api/auth/login` | Ouvrir une session |
| POST | `/api/auth/logout` | Fermer la session |
| GET | `/api/auth/me` | Utilisateur courant |
| GET | `/api/categories` | Lister les catégories |
| POST | `/api/categories` | Créer une catégorie |
| DELETE | `/api/categories/<id>` | Supprimer une catégorie vide |
| GET | `/api/images` | Lister la galerie (`limit`, `offset`, `category_id`) |
| POST | `/api/images` | Importer une ou plusieurs images |
| GET | `/api/images/<id>` | Métadonnées d'une image |
| GET | `/api/images/<id>/file` | Aperçu ou téléchargement (`?download=1`) |
| GET | `/api/images/<id>/descriptors` | Calculer les descripteurs d'une image |
| POST | `/api/images/<id>/transform` | Créer une image dérivée |
| DELETE | `/api/images/<id>` | Supprimer une image |
| POST | `/api/features/extract` | Extraire les descripteurs d'un lot d'images |
| POST | `/api/search` | Recherche initiale |
| POST | `/api/search/feedback` | Appliquer une itération FRE |
| GET | `/api/indexed-images/<id>/file` | Aperçu d'une image de l'index GHIM-10K |

### Exemple de requête pour la recherche simple

Requête `multipart/form-data` :

```text
query_image_id = 15      (ou un fichier dans le champ "query")
top_k = 10
```

### Exemple de requête pour la rétroaction

Requête JSON :

```json
{
  "session_id": "3f9c2a...",
  "relevant_ids": [21, 35, 48],
  "non_relevant_ids": [18, 27],
  "top_k": 10
}
```

Le `session_id` est obligatoire : il garantit que le feedback porte sur les résultats de l'itération courante et qu'il appartient à l'utilisateur connecté. Une session est refusée si l'index a changé depuis sa création.

### Exemple de réponse

```json
{
  "session_id": "3f9c2a...",
  "iteration": 1,
  "ignored_non_relevant_count": 2,
  "weights": [10000.0, 1.42, 0.87],
  "results": [
    {
      "id": 21,
      "path": "aircraft/10_5001.jpg",
      "category": "aircraft",
      "distance": 0.125
    }
  ]
}
```

Les valeurs sont uniquement illustratives. `ignored_non_relevant_count` rappelle que les négatives sont reçues mais non utilisées par l'équation (4).

---

## 11. Interface utilisateur : fonctionnalités implémentées

### 11.1. Authentification

- Page de connexion.
- Page d'inscription.
- Gestion des sessions utilisateur.

### 11.2. Galerie d'images

- Afficher les images disponibles, par pages de 24 avec navigation.
- Importer une ou plusieurs images.
- Télécharger une image.
- Supprimer une ou plusieurs images.
- Organiser les images par catégories.
- Créer des catégories et sous-catégories.

### 11.3. Transformation des images

Permettre à l'utilisateur de créer de nouvelles images à partir d'images existantes.

Exemples :

- Recadrage (Crop).
- Redimensionnement (Resize).
- Rotation par multiples de 90°.
- Retournement horizontal ou vertical.

L'originale est toujours conservée; la copie transformée est enregistrée comme image dérivée.

### 11.4. Visualisation des descripteurs

Pour chaque image, afficher les caractéristiques extraites :

- Histogramme de couleurs.
- Moments de couleur.
- Couleurs dominantes.
- Propriétés GLCM.
- Histogramme LBP.

### 11.5. Recherche simple

L'utilisateur sélectionne une image et le système affiche les images les plus similaires.

Cette recherche sert de point de départ avant l'utilisation de FRE.

### 11.6. Recherche avec Relevance Feedback

L'interface doit permettre à l'utilisateur de :

1. Visualiser les résultats initiaux.
2. Sélectionner les images pertinentes.
3. Sélectionner les images non pertinentes.
4. Valider sa sélection.
5. Consulter les nouveaux résultats.
6. Répéter le processus.

Il est important de distinguer visuellement les images sélectionnées comme pertinentes et celles sélectionnées comme non pertinentes.

---

## 12. Organisation actuelle du dépôt

```text
galerie-gestion/
├── backend/
│   ├── app.py
│   ├── database/
│   │   ├── connection.py
│   │   └── repositories/
│   │       ├── gallery.py
│   │       ├── search_sessions.py
│   │       └── users.py
│   ├── domain/
│   │   ├── features.py
│   │   ├── fre.py
│   │   ├── fre_config.py
│   │   ├── models.py
│   │   ├── normalization.py
│   │   └── retrieval.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── features.py
│   │   ├── gallery.py
│   │   ├── health.py
│   │   └── search.py
│   ├── services/
│   │   ├── evaluation.py
│   │   ├── auth.py
│   │   ├── features.py
│   │   ├── gallery.py
│   │   ├── indexing.py
│   │   └── search.py
│   ├── utils/
│   │   └── image_io.py
│   ├── static/react/    # Bundle compilé par Vite
│   ├── templates/
│   └── __init__.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       ├── main.jsx
│       ├── styles.css
│       └── components/
├── docs/
│   ├── README_IMPLEMENTATION.md
│   ├── explication.md
│   └── references/
│       └── Reweighing Strategies for Relevance  Feedback in CBIR.pdf
├── tests/
│   ├── test_api.py
│   ├── test_evaluation.py
│   ├── test_features.py
│   └── test_fre.py
├── .gitignore
├── README.md
├── requirements.txt
└── requirements-dev.txt
```

Les routes prennent en charge HTTP, les services orchestrent les cas d'usage, les repositories isolent les requêtes SQLite et le domaine regroupe les modèles et calculs CBIR/FRE.

Le dossier `GHIM-10K/` et les dossiers `instance/` présents localement sont ignorés par Git : ils contiennent respectivement le dataset, l'index généré et les données locales de l'application. Ils ne doivent pas être ajoutés au livrable final.

---

## 13. Plan de réalisation du travail

Le développement est organisé en sept phases. Toutes sont implémentées; les tests et l'évaluation sont reproductibles via `pytest` et `python -m backend.services.evaluation`.

### Phase 1 : Étude et préparation

- Lire et comprendre le papier scientifique.
- Comprendre les principes du CBIR.
- Étudier les descripteurs de couleur et de texture.
- Télécharger et analyser le dataset GHIM-10K.
- Définir l'architecture du projet.

**Résultat attendu :** environnement de travail préparé et architecture définie.

### Phase 2 : Extraction des caractéristiques

- Implémenter les histogrammes de couleurs.
- Implémenter les moments de couleur.
- Identifier les couleurs dominantes.
- Implémenter les propriétés GLCM.
- Implémenter les histogrammes LBP.
- Normaliser les caractéristiques.
- Tester l'extraction sur plusieurs images.

**Résultat attendu :** chaque image est représentée par un vecteur de caractéristiques.

### Phase 3 : Recherche simple

- Sélectionner une image requête.
- Extraire son vecteur.
- Comparer ce vecteur avec ceux de la base.
- Calculer les distances.
- Trier les résultats.
- Afficher les images les plus similaires.

**Résultat attendu :** un moteur de recherche CBIR fonctionnel sans rétroaction.

### Phase 4 : Implémentation de FRE

Cette phase constitue le cœur scientifique du travail attribué au groupe.

- Collecter les images pertinentes sélectionnées par l'utilisateur.
- Calculer les moyennes des caractéristiques pertinentes.
- Calculer l'écart-type de chaque dimension.
- Calculer les poids avec la formule FRE.
- Mettre à jour le vecteur de requête.
- Implémenter la distance euclidienne quadratique pondérée.
- Relancer la recherche.
- Gérer plusieurs itérations de rétroaction.

**Résultat attendu :** un moteur de recherche qui améliore ses résultats en exploitant les retours de pertinence.

### Phase 5 : Développement de l'API

- Créer l'application Flask.
- Configurer Flask-RESTful.
- Développer les endpoints.
- Intégrer l'extraction des caractéristiques.
- Intégrer la recherche simple.
- Intégrer FRE.
- Tester les échanges entre l'API et l'application web.

**Résultat attendu :** une API REST fonctionnelle.

### Phase 6 : Développement de l'application web

- Développer l'authentification.
- Développer la galerie.
- Ajouter la gestion des catégories.
- Ajouter les opérations sur les images.
- Ajouter les transformations.
- Ajouter l'affichage des descripteurs.
- Ajouter la recherche simple.
- Ajouter l'interface de rétroaction FRE.

**Résultat attendu :** une application web intégrant toutes les fonctionnalités demandées.

### Phase 7 : Tests et évaluation

- Tester l'extraction des caractéristiques.
- Tester la recherche simple.
- Tester le calcul des poids.
- Tester les distances pondérées.
- Tester plusieurs itérations FRE.
- Comparer les résultats avant et après rétroaction.
- Mesurer les performances du système.

**Résultat attendu :** une application testée et une évaluation expérimentale de la méthode.

---

## 14. Évaluation des résultats

Le papier utilise principalement les mesures de précision et de rappel pour évaluer les systèmes de recherche d'images.

### 14.1. Precision

La précision représente la proportion d'images pertinentes parmi les images retournées.

\[
Precision =
\frac{\text{Nombre d'images pertinentes retrouvées}}
{\text{Nombre total d'images retournées}}
\]

### 14.2. Recall

Le rappel représente la proportion d'images pertinentes retrouvées parmi toutes les images pertinentes disponibles dans la base.

\[
Recall =
\frac{\text{Nombre d'images pertinentes retrouvées}}
{\text{Nombre total d'images pertinentes dans la base}}
\]

### 14.3. Comparaison avant et après FRE

Il est important de comparer deux situations :

**Situation 1 : recherche sans rétroaction**

- Recherche initiale.
- Distance classique.
- Classement des résultats.

**Situation 2 : recherche avec FRE**

- Sélection des images pertinentes.
- Calcul des poids.
- Mise à jour du vecteur de requête.
- Distance pondérée.
- Nouveau classement.

Exemple de tableau pour présenter les résultats expérimentaux :

| Méthode | Precision@10 | Recall@10 |
|---|---:|---:|
| Recherche simple | 0,3336 ± 0,0206 | 0,00669 ± 0,00041 |
| FRE - Itération 1 | 0,4610 ± 0,0365 | 0,00924 ± 0,00073 |
| FRE - Itération 2 | 0,4842 ± 0,0387 | 0,00970 ± 0,00077 |
| FRE - Itération 3 | 0,4844 ± 0,0405 | 0,00971 ± 0,00081 |

Ces valeurs proviennent de cinq tirages reproductibles de 100 requêtes (graines 42 à 46) sur GHIM-10K, avec \(N=10\) et une fenêtre de feedback de 10 résultats, identique à ce que l'interface affiche. Le détail du protocole est décrit dans `README_IMPLEMENTATION.md`.

**Important :** Les performances annoncées dans le papier scientifique correspondent à ses propres expériences et à sa propre base de données. Elles ne doivent pas être présentées comme des résultats obtenus sur GHIM-10K.

---

## 15. Difficultés techniques à anticiper

Les points suivants doivent être pris en considération pendant le développement :

- Les différents descripteurs peuvent avoir des dimensions et des échelles différentes.
- La normalisation est importante pour rendre les distances comparables.
- Le calcul des caractéristiques sur une grande collection d'images peut prendre du temps.
- Il est préférable de pré-calculer les descripteurs de la base.
- Le système doit gérer le cas où aucune image pertinente n'est sélectionnée.
- Le calcul de l'écart-type doit être stable, même avec peu d'images pertinentes.
- Les poids doivent être correctement associés aux dimensions des vecteurs.
- La recherche doit pouvoir être répétée avec plusieurs itérations de rétroaction.
- Les images téléchargées et transformées doivent être correctement identifiées et stockées.

---

## 16. Livrables attendus

Conformément aux consignes du projet, les livrables comprennent :

### 1. Rapport

Un rapport au format `.doc` ou `.pdf` présentant :

- La présentation du projet.
- Les concepts fondamentaux du CBIR.
- Les descripteurs visuels utilisés.
- L'étude du papier scientifique.
- L'explication de la méthode FRE.
- L'architecture du système.
- Les choix techniques.
- L'implémentation.
- Les résultats expérimentaux.
- Une conclusion.

### 2. Dossier du projet

Le dossier doit contenir :

- Le code source de l'application web.
- Le code source de l'API Flask.
- Les modules d'extraction des caractéristiques.
- L'implémentation de la recherche simple.
- L'implémentation de FRE.
- Les fichiers de configuration nécessaires.
- Les dépendances.
- Les tests.
- Un README expliquant l'installation et l'exécution.

**À exclure du dossier final :**

- Le sous-dossier contenant le dataset GHIM-10K.
- Les sous-dossiers générés volumineux.
- Les fichiers temporaires et caches inutiles.

---

## 17. Technologies et bibliothèques possibles

| Technologie | Utilisation |
|---|---|
| Python | Traitement des images et algorithmes |
| Flask | Création de l'API |
| Flask-RESTful | Gestion des endpoints REST |
| NumPy | Manipulation des vecteurs et calculs numériques |
| Pillow | Lecture, transformation et stockage des images |
| React + Vite | Interface utilisateur |
| SQLite | Gestion des utilisateurs, images, catégories et sessions |
| pytest | Tests automatisés |

L'extraction GLCM et LBP est implémentée directement avec NumPy : OpenCV, scikit-image, scikit-learn et Matplotlib ne sont pas utilisés dans l'implémentation actuelle. Les histogrammes sont dessinés dans le navigateur avec l'API Canvas.

---

## 18. Conclusion

Ce projet consiste à développer un système complet de gestion et de recherche d'images basé sur le contenu visuel.

La première partie du travail concerne la gestion des images et l'extraction des descripteurs de couleur et de texture.

La deuxième partie concerne la recherche d'images similaires à partir d'une image requête.

Enfin, la méthode **Feature Relevance Estimation (FRE)** permet d'améliorer cette recherche grâce à la rétroaction de l'utilisateur. Elle estime l'importance des caractéristiques visuelles à partir des images pertinentes, ajuste les poids et utilise une distance pondérée pour classer les résultats.

Le principal objectif de notre groupe est donc de développer et d'évaluer cette méthode, tout en l'intégrant dans une application web fonctionnelle.

---

## Références

1. Renuka Devi SM, *Reweighing Strategies for Relevance Feedback in CBIR*, International Journal of Advanced Research in Computer and Communication Engineering (IJARCCE), Vol. 5, Issue 11, November 2016.
2. Dataset GHIM-10K : https://www.kaggle.com/datasets/mcpython/ghim-10k

