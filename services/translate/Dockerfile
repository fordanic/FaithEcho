FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY pyproject.toml poetry.lock ./
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir poetry && \
    poetry self add poetry-plugin-export && \
    poetry export --without-hashes -f requirements.txt > requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

FROM base AS test
RUN ["python", "-m", "pip", "check"]

FROM base AS runtime
COPY services/translate /app/services/translate
COPY services/utils.py /app/services/utils.py
RUN adduser --disabled-password --uid 1000 appuser && chown -R 1000:1000 /app
USER 1000:1000
CMD ["uvicorn", "services.translate.main:app", "--host", "0.0.0.0", "--port", "8000"]
