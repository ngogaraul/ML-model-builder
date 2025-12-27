# ML Model Builder

This repository contains a simple ML model builder with a Flask backend and a React + Vite frontend.

Contents
- `ml-builder-backend/`: Flask API and ML model code (training, preprocessing, saving models)
- `model-builder-frontend/`: React + Vite frontend that interacts with the backend
- `datasets/`: sample datasets (CSV). Larger CSVs are ignored by `.gitignore` by default.

Quick overview
- The backend exposes endpoints under `/api/*` for uploading datasets, configuring preprocessing, training models (Perceptron, Decision Tree, MLP), viewing metrics/confusion matrix, and saving trained models to `saved_models/`.
- The frontend is a small React app (Vite) that provides a UI to upload data and run experiments.

Requirements
- Python 3.10+ (or compatible 3.x)
- Node.js 18+ / npm

Backend (ml-builder-backend)

1. Create and activate a Python virtual environment (PowerShell example):

```powershell
cd "D:\4th year\ML\ML project\ml-builder-backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the Flask API locally:

```powershell
# from ml-builder-backend folder
$env:FLASK_APP = 'app.py'
python app.py
```

Default host/port can be configured with the `HOST` and `PORT` environment variables. The app listens on port `5000` by default.

Optional environment variables
- `REDIS_URL`: when set, session state can be persisted to Redis.
- `ALLOW_DEBUG_SESSIONS=1`: only set in development to enable the `/api/debug/sessions` endpoint.

Frontend (model-builder-frontend)

1. Install dependencies and run dev server:

```powershell
cd "D:\4th year\ML\ML project\model-builder-frontend"
npm install
npm run dev
```

2. Build for production:

```powershell
npm run build
```

The frontend expects the backend API to be reachable (CORS is enabled in the Flask app). If running backend on a different host/port, update the API base URL in the frontend API helper: `model-builder-frontend/src/api/modelBuilderApi.js`.

API Endpoints (summary)
- `POST /api/upload` — upload CSV/Excel file (multipart form-data, field `file`); returns a `session_id` and data preview.
- `POST /api/preprocess` — configure preprocessing for a `session_id` (JSON body: `session_id`, `method`, `target_column`).
- `POST /api/train` — train a model (JSON body: `session_id`, `model_type`, optional hyperparams).
- `POST /api/save_model` — save trained model to `saved_models/` (JSON body: `session_id`, `model_type`, `model_name`).
- `GET /api/health` — health check.

Project structure notes
- `ml-builder-backend/ml_models/` contains `preprocessing.py` and `classifiers.py` implementing preprocessing pipelines and model wrappers.
- Trained models are saved as joblib files in `saved_models/` by default.
- The frontend includes `README.docker.md` and `nginx.conf` if you want to containerize or serve the built app with Nginx.

Adding your own datasets
- Place CSVs into `datasets/` if you want to use them locally. Note: `.gitignore` excludes `datasets/*.csv` by default to avoid committing large data files.

Suggested next steps
- Update local git user config with your name/email:

```powershell
git config --local user.name "Your Name"
git config --local user.email "you@domain.com"
```

- Consider adding a short `CONTRIBUTING.md` and license file.

Contact / Credits
- This project was developed as part of a machine learning course project. Update this README with your name and repository description before sharing.
