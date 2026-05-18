FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Placeholder until P6 wires the real application entrypoint
COPY docker/backend/health_app.py /app/health_app.py

EXPOSE 8000

CMD ["uvicorn", "health_app:app", "--host", "0.0.0.0", "--port", "8000"]
