# Dockerfile for Technical Document Management API

# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . ./

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 
# Expose the port
EXPOSE 8080

# Run the FastAPI app with Uvicorn
CMD exec uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
