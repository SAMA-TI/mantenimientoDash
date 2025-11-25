FROM python:3.12-slim

WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files and Analisis6 folder (including xlsx files)
COPY requirements.txt .
COPY *.py .
COPY *.xlsx .
COPY config.py .

# Expose port 8000
EXPOSE 8000

# Use gunicorn as entrypoint with 4 workers
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "TableroMantenimiento:server"]