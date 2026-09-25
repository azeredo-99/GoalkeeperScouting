# Imagem única da demo pública: build do React + API FastAPI que o serve.
# Um só serviço (Render), um só URL, sem base de dados gerida -- os dados
# vêm do snapshot data/demo/gk_performances.csv convertido para SQLite no
# build (ver scripts/build_demo_db.py).

# --- 1. Frontend --------------------------------------------------------
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# URL vazio = pedidos relativos (/api/...) ao mesmo domínio que serve a app.
ENV VITE_API_URL=""
RUN npm run build

# --- 2. API ---------------------------------------------------------------
FROM python:3.14-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATABASE_URL=sqlite:////app/data/demo/gk_performances.sqlite \
    FRONTEND_DIST=/app/frontend_dist

COPY requirements-api.txt ./
RUN pip install -r requirements-api.txt

COPY src/ ./src/
COPY scripts/ ./scripts/
COPY data/demo/ ./data/demo/
RUN python scripts/build_demo_db.py

# Base Transfermarkt descarregada no build (e não em cada cold start).
RUN python -c "import sys; sys.path.insert(0, 'src'); from gk_scouting.market_data import load_transfermarkt_players as f; assert len(f()) > 0"

COPY --from=frontend /frontend/dist ./frontend_dist

EXPOSE 8000
CMD ["sh", "-c", "uvicorn gk_scouting.api.main:app --app-dir src --host 0.0.0.0 --port ${PORT:-8000}"]
