# Root Dockerfile so a Render Docker service at repo root can find it.
# Preferred on Free Tier: Native Python (see render.yaml), not this image.
FROM python:3.12-slim

WORKDIR /app/backend

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1
ENV EMBEDDING_PROVIDER=huggingface

COPY backend/requirements.txt backend/requirements-render.txt /app/backend/
RUN python -m pip install --upgrade pip \
    && python -m pip install --index-url https://download.pytorch.org/whl/cpu torch \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && python -c "from sentence_transformers import SentenceTransformer; print('sentence_transformers import OK')"

COPY backend /app/backend
COPY knowledge-base /app/knowledge-base

RUN mkdir -p /app/backend/static/audio /app/backend/logs

EXPOSE 8000

CMD ["python", "start.py"]
