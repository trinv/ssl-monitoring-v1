#!/bin/bash

#############################################
# SSL Monitor - Automated Deployment Script
# For deploying on a new Docker environment
#############################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
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
    echo -e "${BLUE}[$1/$2] $3${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_step 1 9 "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        exit 1
    fi
    print_info "Docker: $(docker --version)"

    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed!"
        exit 1
    fi
    print_info "Docker Compose: $(docker compose version)"

    print_success "Prerequisites check passed"
    echo ""
}

# Stop existing services
stop_services() {
    print_step 2 9 "Stopping existing services (if any)..."
    docker compose down 2>/dev/null || true
    print_success "Services stopped"
    echo ""
}

# Build images
build_images() {
    print_step 3 9 "Building Docker images..."
    print_info "This may take 2-3 minutes on first run..."

    if docker compose build; then
        print_success "Images built successfully"
    else
        print_error "Failed to build images"
        exit 1
    fi
    echo ""
}

# Start services
start_services() {
    print_step 4 9 "Starting all services..."

    if docker compose up -d; then
        print_success "Services started"
    else
        print_error "Failed to start services"
        exit 1
    fi
    echo ""
}

# Wait for PostgreSQL
wait_for_postgres() {
    print_step 5 9 "Waiting for PostgreSQL to be ready..."

    max_attempts=30
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker exec ssl-monitoring-postgres pg_isready -U ssluser >/dev/null 2>&1; then
            print_success "PostgreSQL is ready"
            echo ""
            return 0
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    echo ""
    print_error "PostgreSQL did not become ready in time"
    print_info "Check logs: docker compose logs postgres"
    exit 1
}

# Wait for Backend
wait_for_backend() {
    print_step 6 9 "Waiting for backend to be ready..."

    max_attempts=20
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker logs ssl-monitor-backend 2>&1 | grep -q "FastAPI application started"; then
            print_success "Backend is ready"
            echo ""
            return 0
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    echo ""
    print_error "Backend did not start properly"
    print_info "Check logs: docker compose logs backend"
    exit 1
}

# Run database migrations
run_migrations() {
    print_step 7 9 "Running database migrations..."

    # Run init.sql (domain tables)
    print_info "Creating domain tables..."
    if docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/init.sql >/dev/null 2>&1; then
        print_success "Domain tables created"
    else
        print_info "Domain tables may already exist (this is OK)"
    fi

    # Run auth_migration.sql (auth tables)
    print_info "Creating authentication tables..."
    if docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/auth_migration.sql >/dev/null 2>&1; then
        print_success "Authentication tables created"
    else
        print_info "Authentication tables may already exist (this is OK)"
    fi

    echo ""
}

# Verify deployment
verify_deployment() {
    print_step 8 9 "Verifying deployment..."

    # Check services running
    print_info "Checking services..."
    services_up=$(docker compose ps --format json | jq -r 'select(.State == "running") | .Name' | wc -l)
    if [ "$services_up" -ge 4 ]; then
        print_success "All services are running"
    else
        print_error "Not all services are running"
        docker compose ps
        exit 1
    fi

    # Check backend health
    print_info "Checking backend health..."
    if curl -s http://localhost:8080/health | grep -q "healthy"; then
        print_success "Backend is healthy"
    else
        print_error "Backend health check failed"
        exit 1
    fi

    # Check database tables
    print_info "Checking database tables..."
    table_count=$(docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null || echo "0")
    if [ "$table_count" -ge 8 ]; then
        print_success "Database tables created ($table_count tables)"
    else
        print_error "Expected at least 8 tables, found $table_count"
        exit 1
    fi

    # Check admin user
    print_info "Checking admin user..."
    admin_exists=$(docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -tAc "SELECT COUNT(*) FROM users WHERE username='admin'" 2>/dev/null || echo "0")
    if [ "$admin_exists" -eq 1 ]; then
        print_success "Admin user exists"
    else
        print_error "Admin user not found"
        exit 1
    fi

    echo ""
}

# Display summary
display_summary() {
    print_step 9 9 "Deployment complete!"

    print_header "🎉 SSL Monitor Deployed Successfully!"

    echo -e "${GREEN}Your SSL monitoring system is ready!${NC}"
    echo ""
    echo "📍 Access Information:"
    echo "   Frontend URL: http://$(hostname -I | awk '{print $1}'):8888"
    echo "   API URL:      http://$(hostname -I | awk '{print $1}'):8080"
    echo "   API Docs:     http://$(hostname -I | awk '{print $1}'):8080/docs"
    echo ""
    echo "🔐 Login Credentials:"
    echo "   Username: admin"
    echo "   Password: Admin@123"
    echo ""
    echo -e "${RED}⚠️  IMPORTANT: Change the admin password after first login!${NC}"
    echo ""
    echo "📊 Service Status:"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "📝 Useful Commands:"
    echo "   View all logs:     docker compose logs -f"
    echo "   View backend logs: docker compose logs -f backend"
    echo "   Check status:      docker compose ps"
    echo "   Restart services:  docker compose restart"
    echo "   Stop services:     docker compose down"
    echo ""
    echo -e "${GREEN}Happy monitoring! 🔐✨${NC}"
}

# Main deployment flow
main() {
    print_header "SSL Monitor - Automated Deployment"

    check_prerequisites
    stop_services
    build_images
    start_services
    wait_for_postgres
    wait_for_backend
    run_migrations
    verify_deployment
    display_summary
}

# Run main function
main
