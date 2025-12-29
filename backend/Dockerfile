# Backend Dockerfile for Recipe Recommender
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data

# Create entrypoint script
RUN echo '#!/bin/bash\nset -e\npython startup.py\nexec python app.py' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Run the application with startup initialization
CMD ["/bin/bash", "/app/entrypoint.sh"]
