# Use slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Create data directory for JSON storage
RUN mkdir -p /app/data

# Koyeb uses PORT env variable (default 8000)
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run with gunicorn (production-ready)
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app
