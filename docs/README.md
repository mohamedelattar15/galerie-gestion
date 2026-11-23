# Documentation du projet

Cette documentation décrit le projet **tel qu’il est implémenté**. Le [`README.md`](../README.md) à la racine est le point d’entrée GitHub et contient le démarrage rapide.

## Guides

| Document | Sujet |
|---|---|
| [STACK.md](STACK.md) | Technologies, dépendances et responsabilités de chaque outil. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Organisation frontend, API, domaine, données et parcours d’une recherche. |
| [METHODS.md](METHODS.md) | Descripteurs, traitement du fond, normalisation, distance et méthode FRE de G13. |
| [OBJECT_AND_BACKGROUND.md](OBJECT_AND_BACKGROUND.md) | Algorithme de masque, séparabilité du fond, modes variance/adaptatif, échecs et pistes de correction. |
| [API.md](API.md) | Routes HTTP, paramètres importants et conventions d’authentification. |
| [PROBLEMS_AND_SOLUTIONS.md](PROBLEMS_AND_SOLUTIONS.md) | Problématique CBIR, problèmes traités, solutions et limites connues. |
| [INSTALLATION.md](INSTALLATION.md) | Environnement, installation, indexation, exécution et configuration. |
| [EVALUATION.md](EVALUATION.md) | Protocole hors ligne, résultats connus, interprétation et reproductibilité. |

## Documents antérieurs

- [`explication.md`](explication.md) présente en détail le CBIR, l’article de référence et FRE. Il constitue une explication pédagogique complémentaire.
- [`README_IMPLEMENTATION.md`](README_IMPLEMENTATION.md) conserve le plan initial de réalisation et des propositions de conception. Certaines sections décrivent des choix proposés ou un état antérieur; pour connaître le fonctionnement actuel, utiliser en priorité les guides ci-dessus et le code source.
- Le PDF de l’article fourni est conservé dans [`references/`](references/).

Les scripts, paramètres et chemins mentionnés dans les guides sont à vérifier avec le dépôt si l’implémentation évolue. Les fichiers du dataset, SQLite, téléversements et index sont générés ou ajoutés localement et ne doivent pas être commités.
