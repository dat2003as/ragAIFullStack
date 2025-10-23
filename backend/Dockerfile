# backend/Dockerfile
FROM python:3.11.13-slim

WORKDIR /app

# Install system dependencies including curl for healthcheck
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directories
RUN mkdir -p uploads/images uploads/csv uploads/documents

# Expose ports
EXPOSE 8000 8001

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]