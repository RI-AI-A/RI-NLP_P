# NLP Backend Dockerfile
FROM python:3.10-slim

# Install system dependencies including ffmpeg for audio processing
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install setuptools first to avoid pkg_resources issues
RUN pip install --no-cache-dir setuptools wheel

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model (will be done at runtime if needed)
# RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/audio data/faiss_index

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "api_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
