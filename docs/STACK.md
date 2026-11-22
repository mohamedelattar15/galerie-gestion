# Stack technique

## Technologies utilisées

| Couche | Technologie | Rôle dans l’application |
|---|---|---|
| Interface | React 19 | Composants d’authentification, galerie, recherche et fiche image. |
| Outil frontend | Vite 7 | Serveur de développement et compilation de l’application statique. |
| API et serveur | Python 3.12+, Flask 3 | Configuration de l’application, sessions HTTP, routes et service du frontend compilé. |
| Ressources REST | Flask-RESTful | Ressources `/health`, extraction des descripteurs, recherche et feedback. Les autres routes sont organisées en Blueprints Flask. |
| Traitement des images | Pillow | Lecture/validation des images et transformations. |
| Calcul numérique | NumPy | Descripteurs, normalisation, distances, index et métriques d’évaluation. |
| Données applicatives | SQLite | Comptes, catégories, métadonnées d’images et sessions FRE. |
| Fichiers | Système de fichiers local | Images importées et images dérivées. |
| Index de recherche | NumPy `.npz` compressé | Vecteurs normalisés, chemins, catégories et paramètres de normalisation. |
| Icônes | lucide-react | Icônes de l’interface. |

## Dépendances Python

Les dépendances applicatives sont définies dans `requirements.txt` : Flask, Flask-RESTful, NumPy et Pillow. `requirements-dev.txt` ajoute pytest pour les tests.

## Dépendances frontend

Le fichier `frontend/package.json` définit React, React DOM, Vite, le plugin React pour Vite et lucide-react. L’installation crée `frontend/node_modules/`; la compilation place le frontend dans `backend/static/react/`, chemin exclu de Git.

## Pourquoi cette stack ?

Flask reçoit les appels HTTP et expose les fonctions du moteur de recherche. NumPy rend possible le calcul vectorisé sur les 10 000 descriptions du corpus sans base vectorielle dédiée pour ce prototype. SQLite et les fichiers locaux simplifient l’exécution et la remise universitaire. React isole les vues et permet une interface interactive.

Ces choix conviennent à un prototype pédagogique local. Un déploiement multi-utilisateur à grande échelle nécessiterait notamment un stockage objet, une base serveur adaptée, une configuration de sécurité et une stratégie de calcul asynchrone.
