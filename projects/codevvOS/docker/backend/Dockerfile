FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Install esbuild for JSX compilation (keep curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && curl -fsSL https://esbuild.github.io/dl/latest | sh \
    && mv ./esbuild /usr/local/bin/esbuild \
    && chmod +x /usr/local/bin/esbuild \
    && rm -rf /var/lib/apt/lists/*
COPY backend/ backend/
COPY shared/ shared/
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
