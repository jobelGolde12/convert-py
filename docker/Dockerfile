FROM python:3.11-slim

# System deps: LibreOffice + curl (healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libreoffice \
      libreoffice-writer \
      fonts-inter \
      curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml ./
COPY app ./app

# Run as an unprivileged user; storage dir must be writable.
RUN useradd --create-home --uid 10001 convert \
    && mkdir -p /app/storage /tmp/lo-profiles \
    && chown -R convert:convert /app/storage /tmp/lo-profiles
USER convert

ENV PYTHONUNBUFFERED=1 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
