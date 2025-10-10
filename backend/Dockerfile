# Use miniconda base image
FROM continuumio/miniconda3:latest

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    CONDA_DEFAULT_ENV=runner \
    CONDA_AUTO_ACTIVATE_BASE=false

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create conda environment named 'runner'
RUN conda create -n runner python=3.11 -y

# Activate runner environment and install dependencies
SHELL ["conda", "run", "-n", "runner", "/bin/bash", "-c"]

# Copy requirements and install Python dependencies in runner environment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Create necessary directories
RUN mkdir -p /app/temp /app/data

# Expose port
EXPOSE 8000

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Switch to non-root user
USER app

# Initialize conda for the non-root user
RUN /opt/conda/bin/conda init bash

# Health check (using conda to run the health check)
SHELL ["conda", "run", "-n", "runner", "/bin/bash", "-c"]
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application in runner environment
CMD ["conda", "run", "-n", "runner", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]