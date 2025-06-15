# Tests for Technical Document Management System

This directory contains tests for the Technical Document Management System.

## Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_similarity.py

# Run with coverage
python -m pytest --cov=src tests/

# Generate coverage report
python -m pytest --cov=src --cov-report=html tests/
```

## Test Structure

- `test_similarity.py`: Tests for document similarity functionality
- `test_processor.py`: Tests for document processing functionality
- `test_agent.py`: Tests for the ADK agent functionality

## Mock Data

Test fixtures provide mock data for various components, including:
- Document embeddings
- Document AI responses
- Vision API responses
- Search results

## Running Integration Tests

Some tests may require actual Google Cloud resources. To run these tests:

1. Set up proper credentials:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
   ```

2. Run integration tests:
   ```bash
   python -m pytest tests/ -m integration
   ```
