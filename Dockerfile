# Dockerfile for Technical Document Management API

# Use Python 3.9 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY ./src/requirements.txt ./
COPY ./credentials ./credentials
COPY ./src/.env ./.env
# Copy the application code
COPY ./src/document-management-ui ./document-management-ui

# Install dependencies
RUN pip install --no-cache-dir -r ./requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 
# Expose the port
EXPOSE 8080

# Run the FastAPI app with Uvicorn
CMD exec streamlit run --server.headless true --server.address 0.0.0.0 --server.port $PORT ./document-management-ui/streamlit.py
