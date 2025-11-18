# Use Python 3.10 slim image (compatible with pysha3)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    python3-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r agents/requirements.txt

# Set environment variables
ENV PYTHONPATH=/app/agents
ENV PYTHONUNBUFFERED=1

# Change to agents directory and run the continuous scanner
WORKDIR /app/agents
CMD ["python", "run_continuous.py", "--interval", "15"]
