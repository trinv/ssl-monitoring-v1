FROM python:3.11-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy scanner script
COPY scanner.py /app/

# Run scanner
CMD ["python", "/app/scanner.py"]
