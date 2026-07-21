# Production container image for the Sudoku Flask app.
# Targets Google Cloud Run, which expects the app to listen on $PORT (default 8080).
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer). Add gunicorn for production WSGI serving.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==21.2.0

# Copy application code. Be selective so the image stays lean.
COPY app.py sudoku.py storage.py ./
COPY static/ ./static/
COPY templates/ ./templates/

# Cloud Run injects PORT=8080 by default.
ENV PORT=8080
EXPOSE 8080

# Run with gunicorn. One worker + multiple threads suits a small sync Flask app on Cloud Run.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]
