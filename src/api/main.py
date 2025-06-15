"""
Main API module for technical document management system.
"""
import os
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, UploadFile, File, Form, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
import uvicorn

# Import routes
from .routes import documents, search, agent

# Create FastAPI app
app = FastAPI(
    title="Technical Document Management API",
    description="API for managing and searching technical documents",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])

@app.get("/")
async def root():
    """Root endpoint that returns API information."""
    return {
        "name": "Technical Document Management API",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8080))
    
    # Start the server
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
