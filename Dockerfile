FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y kubernetes onnxruntime pydeck ruff pytest \
    && find /usr/local/lib/python3.11 -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.11 -type d -name "test" -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.11 -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.11 -name "*.pyc" -delete \
    && find /usr/local/lib/python3.11 -name "*.pyo" -delete \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /root/.cache

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000 8501 7860

ENTRYPOINT ["./entrypoint.sh"]
