FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    bash \
    openssl \
    curl \
    postgresql-client \
    bc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy scanner script
COPY scanner.sh /app/

# Make executable
RUN chmod +x /app/scanner.sh

# Run scanner
CMD ["/app/scanner.sh"]
