Docker — build and run (production)

This repo is a Vite React frontend. The Docker setup builds static assets and serves them with `nginx`.

Build image (from repo root):

```powershell
# Build image locally
docker build -t model-builder-frontend:latest .
```

Run container (map host port 5173 -> container port 80):

```powershell
# Run container
docker run --rm -p 5173:80 model-builder-frontend:latest
```

Or use docker-compose (build + run):

```powershell
docker-compose up --build
```

Notes
- `nginx.conf` proxies `/api` to `http://host.docker.internal:5000/` so the container can reach a backend running on your host machine. If your backend runs in another container, update `nginx.conf` or add the backend service to `docker-compose.yml`.
- If you prefer to run the Vite dev server inside a container (for live reload), tell me and I can add a `docker-compose.dev.yml` that runs `npm run dev` and forwards ports accordingly.
