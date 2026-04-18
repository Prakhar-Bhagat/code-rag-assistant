FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1
# Install system dependencies for tree-sitter and python builds
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Use 'python -m uvicorn' to ensure it uses the installed package in the path
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]