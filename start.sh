#!/bin/bash

###############################################
# SSL Monitor - Complete Deployment Script
# For fresh installation on Linux with Docker
###############################################

set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "$1"
    echo "=============================================="
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${BLUE}[Step $1/$2] $3${NC}"
}

# Error handler
error_exit() {
    print_error "$1"
    echo ""
    echo "Deployment failed. Check the error above."
    echo "You can check logs with: docker compose logs"
    exit 1
}

# Main deployment
main() {
    print_header "SSL Monitor - Complete Deployment"
    echo "This script will deploy everything from scratch"
    echo ""

    # Step 1: Check prerequisites
    print_step 1 8 "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed! Please install Docker first."
    fi
    print_info "Docker: $(docker --version)"

    if ! docker compose version &> /dev/null; then
        error_exit "Docker Compose is not installed! Please install Docker Compose first."
    fi
    print_info "Docker Compose: $(docker compose version)"

    print_success "Prerequisites OK"
    echo ""

    # Step 2: Clean up old containers and volumes (if any)
    print_step 2 8 "Cleaning up old containers and volumes..."
    docker compose down -v 2>/dev/null || true
    print_success "Cleanup complete"
    echo ""

    # Step 3: Build Docker images
    print_step 3 8 "Building Docker images..."
    print_info "This may take 2-3 minutes on first run..."

    if ! docker compose build; then
        error_exit "Failed to build Docker images"
    fi
    print_success "Images built successfully"
    echo ""

    # Step 4: Start services
    print_step 4 8 "Starting all services..."

    if ! docker compose up -d; then
        error_exit "Failed to start services"
    fi
    print_success "Services started"
    echo ""

    # Step 5: Wait for PostgreSQL to be ready
    print_step 5 8 "Waiting for PostgreSQL to be ready..."

    max_attempts=30
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker exec ssl-monitoring-postgres pg_isready -U ssluser -d ssl_monitor >/dev/null 2>&1; then
            print_success "PostgreSQL is ready"
            break
        fi

        attempt=$((attempt + 1))
        if [ $attempt -eq $max_attempts ]; then
            error_exit "PostgreSQL did not become ready in time"
        fi

        echo -n "."
        sleep 2
    done
    echo ""
    echo ""

    # Step 6: Wait for Backend to start
    print_step 6 8 "Waiting for backend to start..."

    max_attempts=20
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker logs ssl-monitor-backend 2>&1 | grep -q "Application startup complete"; then
            print_success "Backend is ready"
            break
        fi

        attempt=$((attempt + 1))
        if [ $attempt -eq $max_attempts ]; then
            print_error "Backend may have issues, but continuing..."
            break
        fi

        echo -n "."
        sleep 2
    done
    echo ""
    echo ""

    # Step 7: Initialize database schema
    print_step 7 8 "Initializing database..."

    # Run init.sql (domain tables) - automatically run by docker-entrypoint
    print_info "Domain tables created automatically on first start"

    # Run auth migration (create auth tables)
    print_info "Creating authentication tables..."
    if docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/simple_auth_migration.sql >/dev/null 2>&1; then
        print_success "Authentication tables created"
    else
        error_exit "Failed to create authentication tables"
    fi
    echo ""

    # Step 8: Verify deployment
    print_step 8 8 "Verifying deployment..."

    # Check all services are running
    print_info "Checking services..."
    running_services=$(docker compose ps --format json 2>/dev/null | grep -c '"State":"running"' || echo "0")

    if [ "$running_services" -ge 4 ]; then
        print_success "All services are running ($running_services services)"
    else
        print_error "Not all services are running"
        docker compose ps
    fi

    # Check backend health
    print_info "Checking backend health..."
    sleep 3
    if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
        print_success "Backend health check passed"
    else
        print_error "Backend health check failed, but continuing..."
    fi

    # Check database tables
    print_info "Checking database tables..."
    table_count=$(docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null || echo "0")

    if [ "$table_count" -ge 5 ]; then
        print_success "Database tables created ($table_count tables)"
    else
        print_error "Expected at least 5 tables, found $table_count"
    fi

    # Check admin user exists
    print_info "Checking admin user..."
    admin_exists=$(docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -tAc "SELECT COUNT(*) FROM users WHERE username='admin'" 2>/dev/null || echo "0")

    if [ "$admin_exists" -eq 1 ]; then
        print_success "Admin user created"
    else
        print_error "Admin user not found"
    fi

    echo ""

    # Display summary
    print_header "🎉 Deployment Complete!"

    echo -e "${GREEN}SSL Monitor is now running!${NC}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")

    echo "📍 Access Information:"
    echo "   Frontend:  http://$SERVER_IP"
    echo "   Backend:   http://$SERVER_IP:8080"
    echo "   API Docs:  http://$SERVER_IP:8080/docs"
    echo ""
    echo "🔐 Login Credentials:"
    echo "   Username: admin"
    echo "   Password: Admin@123"
    echo ""
    echo -e "${RED}⚠️  IMPORTANT: Change admin password after first login!${NC}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📊 Service Status:"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker compose ps
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📝 Useful Commands:"
    echo "   View all logs:      docker compose logs -f"
    echo "   View backend logs:  docker compose logs -f backend"
    echo "   Check status:       docker compose ps"
    echo "   Restart services:   docker compose restart"
    echo "   Stop all:           docker compose down"
    echo "   Stop & clean:       docker compose down -v"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${GREEN}🚀 Ready to monitor SSL certificates!${NC}"
    echo ""
}

# Run main function
main "$@"
