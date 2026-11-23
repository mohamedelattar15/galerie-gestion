# Problèmes relevés et corrections réalisées

Ce document récapitule les problèmes évoqués pendant nos échanges et les corrections intégrées au dépôt. Il distingue une correction fonctionnelle, une amélioration d’interface et une clarification méthodologique : toutes ne changent pas l’algorithme de recherche.

## Corrections réalisées

| Problème observé | Correction réalisée | Où la retrouver |
|---|---|---|
| Une petite couleur vive du sujet était absente des couleurs dominantes, car celles-ci favorisent les grandes surfaces. | Ajout d’une couleur d’accent saturée calculée séparément et affichée dans la fiche de descripteurs. Elle est informative : elle n’est pas incluse dans le vecteur de 329 dimensions et ne participe pas au classement. | `backend/domain/features.py`, `frontend/src/components/ImageDetailPage.jsx`, [METHODS.md](METHODS.md) |
| La séparation sujet/fond pouvait être prise pour une vraie reconnaissance d’objet. | Clarification de la méthode : estimation heuristique depuis les bordures, masque binaire avec garde-fous, et repli par variance. Les limites et pistes de segmentation sont décrites séparément. | [OBJECT_AND_BACKGROUND.md](OBJECT_AND_BACKGROUND.md) |
| Les histogrammes sur la fiche image étaient difficiles à lire et la page de détails manquait de structure. | Réorganisation des outils en sections/onglets et présentation des histogrammes dans des cartes avec axes, légendes et dimensions mieux adaptées. | `frontend/src/components/ImageDetailPage.jsx`, `frontend/src/styles.css` |
| La page Recherche paraissait vide avant la première requête. | Ajout d’un panneau d’accueil qui explique les étapes de recherche et le feedback FRE, avec une mise en page adaptée au viewport et au mobile. | `frontend/src/components/SearchPanel.jsx`, `frontend/src/styles.css` |
| La page Importer paraissait peu remplie et n’expliquait pas le parcours. | Ajout d’un en-tête visuel, d’informations sur l’import par lot et les catégories, et d’étapes « Ajouter, Classer, Explorer ». | `frontend/src/components/Workspace.jsx`, `frontend/src/styles.css` |
| Les boutons d’action de la galerie s’empilaient ou se chevauchaient lorsque l’espace horizontal était réduit. | Maintien des actions sur une ligne défilable, plutôt que de les empiler verticalement. | `frontend/src/styles.css` — `.gallery-bulk-actions` |
| Les cases de sélection des vignettes avaient une taille ou une position incohérente à cause des styles de formulaire généraux. | Dimensions explicites pour la zone de sélection et son input; cible tactile agrandie sur mobile. | `frontend/src/components/GalleryPanel.jsx`, `frontend/src/styles.css` — `.tile-select` |
| Les actions de sélection groupée demandées pour plusieurs images n’étaient pas assez visibles/complètes dans l’interface. | Galerie avec sélection multiple, suppression groupée, déplacement vers une catégorie et téléchargement ZIP; filtres, tri, recherche par nom et pagination. | `frontend/src/components/GalleryPanel.jsx`, `backend/routes/batch.py`, [API.md](API.md) |
| Certaines couleurs d’accent et états de vote manquaient de contraste, surtout en thème sombre. | Tokens de texte distincts des couleurs de fond, états pertinents/non pertinents adaptés au thème, focus visible et cibles tactiles de 44 px sur mobile. | `frontend/src/styles.css` |
| La navigation par onglets à la souris fonctionnait, mais les onglets n’étaient pas parcourables conformément à leur rôle au clavier. | Prise en charge des flèches, de `Home` et `End`, avec un seul onglet actif dans l’ordre de tabulation. | `frontend/src/components/Workspace.jsx`, `frontend/src/components/ImageDetailPage.jsx` |
| L’état d’envoi d’une image ne distinguait pas le transfert réel du traitement côté serveur. | Progression de téléversement basée sur les événements réels du transfert, puis indication du traitement; animations réduites si `prefers-reduced-motion` est activé. | `frontend/src/api.js`, `frontend/src/components/ImageUploader.jsx`, `frontend/src/styles.css` |

## Constats à ne pas confondre avec une correction complète

- La couleur d’accent est maintenant détectée et visible, mais elle n’améliore pas encore la similarité calculée. Pour qu’elle influence le classement, il faudrait l’ajouter comme bloc au vecteur, définir sa normalisation et son poids, reconstruire l’index et comparer les résultats avant/après.
- Le mode adaptatif ne masque pas actuellement tous les descripteurs. En cas de masque accepté, le masque est utilisé pour LBP; les couleurs dominantes et GLCM restent globales. Les histogrammes HSV et moments RGB sont pondérés en mode variance ou en repli adaptatif, mais globaux lorsque le masque adaptatif est accepté.
- Les retours négatifs sont transmis et comptés, mais la formule FRE actuelle utilise les exemples positifs uniquement.
- Le masque objet/fond demeure une heuristique couleur; il ne garantit pas une segmentation correcte sur toutes les images.
- Une amélioration visuelle n’est pas une preuve d’amélioration CBIR. Les nouvelles variantes doivent être évaluées avec des requêtes, K, graines et protocoles de feedback identiques; les résultats automatiques fondés sur les catégories ne remplacent pas un jugement humain.

## État de vérification

Les changements d’interface cités dans ce récapitulatif ont été compilés avec Vite lors de leur implémentation. Ce document n’affirme pas qu’un audit d’accessibilité complet ou une nouvelle évaluation CBIR a été effectué pour chaque changement. Pour les limites et le protocole de mesure, voir [PROBLEMS_AND_SOLUTIONS.md](PROBLEMS_AND_SOLUTIONS.md) et [EVALUATION.md](EVALUATION.md).
