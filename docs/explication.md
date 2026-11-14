# Système de Gestion et de Recherche d’Images par le Contenu (CBIR)

## Projet : Content-Based Image Retrieval avec Feature Relevance Estimation (FRE)

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

### 6.3. Distance euclidienne pondérée

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

Voici le déroulement proposé pour notre système.

### Étape 1 : Préparation de la base d'images

- Charger les images du dataset GHIM-10K.
- Vérifier les formats et les fichiers.
- Extraire les caractéristiques visuelles de chaque image.
- Normaliser les descripteurs.
- Stocker les vecteurs dans une base de données ou un fichier dédié.

### Étape 2 : Recherche initiale

- L'utilisateur sélectionne une image requête.
- Le système extrait son vecteur de caractéristiques.
- Le système compare ce vecteur avec les vecteurs de la base.
- Les distances sont calculées.
- Les images les plus proches sont affichées.

Cette première recherche constitue la référence avant rétroaction.

### Étape 3 : Collecte de la rétroaction

L'utilisateur indique les images :

- Pertinentes (Relevant).
- Non pertinentes (Non-Relevant).

Ces informations sont enregistrées pour l'itération actuelle.

### Étape 4 : Estimation des poids

À partir des images pertinentes, calculer l'écart-type de chaque caractéristique.

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

Les poids peuvent ensuite être normalisés pour faciliter leur utilisation.

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

Le système met à jour les poids et la requête, puis effectue une nouvelle recherche.

Le processus se répète jusqu'à ce que l'utilisateur soit satisfait des résultats.

### Pseudo-code

```text
ALGORITHM Feature_Relevance_Estimation

INPUT:
    Database D
    Query image Q
    Number of results K

OUTPUT:
    Ranked images

1. Extract feature vector FQ from Q

2. For each image I in D:
       Extract or load feature vector FI

3. Perform initial retrieval:
       Compute Euclidean distance between FQ and FI
       Sort images by ascending distance
       Display top K images

4. Collect user feedback:
       R = relevant images
       N = non-relevant images

5. If R is empty:
       Keep the previous search
       Ask for relevant feedback
       Stop or repeat

6. Compute the new query:
       Q_new = Mean(feature vectors of R)

7. Estimate feature weights:
       For each feature dimension i:
           sigma_i = StandardDeviation(R[:, i])
           w_i = 1 / (0.0001 + sigma_i)

8. Normalize weights if necessary

9. Perform weighted retrieval:
       For each image I in D:
           Compute weighted distance between Q_new and FI

10. Sort images by ascending weighted distance

11. Display new results

12. Repeat from step 4 if the user wants another iteration

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

Le projet est organisé autour de deux parties principales : l'application web et l'API de traitement d'images.

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
- Bibliothèques de traitement d'images et d'extraction de caractéristiques.

Elle assure :

- L'extraction des descripteurs.
- La génération des vecteurs de caractéristiques.
- Le calcul des distances.
- L'exécution de l'algorithme FRE.
- Le retour des résultats à l'application web.

### 9.3. Communication entre les composants

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

## 10. API REST : endpoints proposés

Les endpoints suivants constituent une proposition d'organisation de l'API.

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/api/features/extract` | Extraire les descripteurs d'une image |
| POST | `/api/features/extract-batch` | Extraire les descripteurs de plusieurs images |
| GET | `/api/features/<image_id>` | Récupérer les descripteurs d'une image |
| POST | `/api/search` | Effectuer une recherche simple |
| POST | `/api/search/feedback` | Effectuer une recherche avec rétroaction |
| POST | `/api/fre/weights` | Calculer les poids FRE |
| POST | `/api/fre/update-query` | Mettre à jour le vecteur de requête |

### Exemple de requête pour la recherche simple

```json
{
  "query_image_id": 15,
  "top_k": 10
}
```

### Exemple de requête pour la rétroaction

```json
{
  "query_image_id": 15,
  "relevant_ids": [21, 35, 48],
  "non_relevant_ids": [18, 27],
  "iteration": 1,
  "top_k": 10
}
```

### Exemple de réponse

```json
{
  "method": "FRE",
  "iteration": 1,
  "results": [
    {
      "image_id": 21,
      "distance": 0.125
    },
    {
      "image_id": 35,
      "distance": 0.183
    }
  ]
}
```

Les valeurs sont uniquement illustratives. Les résultats réels seront calculés à partir des images et des descripteurs du dataset.

---

## 11. Interface utilisateur : fonctionnalités à développer

### 11.1. Authentification

- Page de connexion.
- Page d'inscription.
- Gestion des sessions utilisateur.

### 11.2. Galerie d'images

- Afficher les images disponibles.
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

Le développement peut être organisé en plusieurs phases.

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
- Implémenter la distance euclidienne pondérée.
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

| Méthode | Precision | Recall |
|---|---:|---:|
| Recherche simple | À mesurer | À mesurer |
| FRE - Itération 1 | À mesurer | À mesurer |
| FRE - Itération 2 | À mesurer | À mesurer |
| FRE - Itération 3 | À mesurer | À mesurer |

Les valeurs doivent être obtenues à partir des expérimentations réalisées sur GHIM-10K.

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
| OpenCV | Lecture et traitement des images |
| scikit-image | Extraction GLCM et LBP |
| scikit-learn | Clustering et outils statistiques |
| Matplotlib | Visualisation des histogrammes |
| Pillow | Manipulation des images |
| Frontend Web | Interface utilisateur |
| Base de données | Gestion des utilisateurs, images et catégories |

Les bibliothèques proposées sont des choix techniques possibles pour réaliser les fonctionnalités demandées.

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

