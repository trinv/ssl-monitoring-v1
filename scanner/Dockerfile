FROM debian:bullseye-slim

# Install required packages for bash scanner
RUN apt-get update && apt-get install -y \
    bash \
    openssl \
    curl \
    postgresql-client \
    bc \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy scanner script
COPY scanner.sh /app/
RUN chmod +x /app/scanner.sh

# Run scanner
CMD ["/app/scanner.sh"]
