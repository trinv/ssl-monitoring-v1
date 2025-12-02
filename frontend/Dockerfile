# ============================================
# Stage 1: Build
# ============================================
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm ci --only=dev

# Copy source code
COPY . .

# Build application
RUN npm run build

# ============================================
# Stage 2: Production
# ============================================
FROM node:18-alpine

WORKDIR /app

# Install serve to serve static files
RUN npm install -g serve@14.2.0

# Copy built files from builder
COPY --from=builder /app/dist ./dist

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

USER nodejs

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD serve --single dist --listen 3000 | grep -q "Accepting" || exit 1

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]