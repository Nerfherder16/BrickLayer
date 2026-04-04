FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 3002
HEALTHCHECK --interval=15s --timeout=5s --retries=3 CMD curl -f http://localhost:3002/health || exit 1
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3002"]
