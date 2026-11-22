# Installation et démarrage

## Prérequis

- Python **3.12 ou plus récent**.
- Node.js et npm (versions compatibles avec Vite 7).
- Une copie de GHIM-10K placée dans `GHIM-10K/` pour la recherche sur le corpus.

L’API peut démarrer sans index, mais la recherche CBIR répondra qu’aucun index n’est chargé. La base SQLite et le répertoire des images importées sont initialisés localement sous `instance/` au premier lancement.

## Windows — PowerShell

À la racine du dépôt :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Set-Location frontend
npm install
npm run build
Set-Location ..
```

Indexer GHIM-10K puis lancer l’application :

```powershell
.\.venv\Scripts\python.exe -m backend.services.indexing --dataset GHIM-10K --output instance\features.npz --mode global
.\.venv\Scripts\python.exe -m backend.app
```

Ouvrir <http://127.0.0.1:5000>.

## Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cd frontend
npm install
npm run build
cd ..
python -m backend.services.indexing --dataset GHIM-10K --output instance/features.npz --mode global
python -m backend.app
```

## Développement avec Vite

Construisez l’index comme ci-dessus. Dans un premier terminal, lancez `python -m backend.app`. Dans un second :

```bash
cd frontend
npm install
npm run dev
```

Vite utilise `http://127.0.0.1:5173` et relaie les requêtes `/api` et `/health` vers le backend local `http://127.0.0.1:5000`.

## Variantes d’index optionnelles

Pour rendre disponibles les choix variance et adaptatif dans la page Recherche, générez également :

```bash
python -m backend.services.indexing --dataset GHIM-10K --output instance/features_variance.npz --mode variance
python -m backend.services.indexing --dataset GHIM-10K --output instance/features_adaptive.npz --mode adaptive
```

Redémarrez Flask après la création de ces index. Il recherche les fichiers de variantes à côté de l’index global. Si un index a été créé avec une ancienne transformation, le chargement échoue volontairement : reconstruisez-le à partir du code actuel.

## Configuration locale

| Variable | Valeur par défaut | Usage |
|---|---|---|
| `SECRET_KEY` | Clé aléatoire au démarrage | Clé de signature des sessions. Configurez une valeur stable hors développement. |
| `DATABASE_PATH` | `instance/cbir.sqlite3` | Chemin du fichier SQLite. |
| `UPLOAD_DIR` | `instance/uploads` | Stockage des images des utilisateurs. |
| `DATASET_DIR` | `GHIM-10K` | Racine du corpus indexé. |
| `CBIR_INDEX_PATH` | `instance/features.npz` | Index global principal. |
| `SEARCH_SESSION_RETENTION_DAYS` | `7` | Durée avant purge des anciennes sessions de recherche. |

Les images importées sont limitées par la configuration Flask à 64 Mo par requête. N’ajoutez pas `GHIM-10K/`, `instance/`, `node_modules/` ou le frontend compilé aux livrables Git.
