FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed.seed && case \"${SEED_BULK:-false}\" in true|1|yes) python -m app.seed.bulk_gen ;; esac && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
