#!/bin/bash

#############################################################################
# SSL Certificate Scanner
# Based on check_ssl_bulk.sh - Uses bash/openssl/curl + PostgreSQL
#############################################################################

# Database configuration
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-ssl_monitor}"
DB_USER="${DB_USER:-ssluser}"
DB_PASSWORD="${DB_PASSWORD:-SSL@Pass123}"

# Scanner configuration
CONCURRENCY="${CONCURRENCY:-20}"
SCAN_INTERVAL="${SCAN_INTERVAL:-3600}"
TIMEOUT="${TIMEOUT:-5}"

# Colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

#############################################################################
# PostgreSQL query helper
#############################################################################
psql_query() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "$1" 2>/dev/null
}

#############################################################################
# Check single domain - EXACTLY like check_ssl_bulk.sh
#############################################################################
check_domain() {
    local DOMAIN="$1"
    local DOMAIN_ID="$2"

    #### 1. Check SSL certificate
    CERT_INFO=$(echo | timeout $TIMEOUT openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null)

    if [[ -z "$CERT_INFO" ]]; then
        echo "RESULT:$DOMAIN_ID|INVALID|NO_SSL|NULL|NO_RESPONSE|-"
        return
    fi

    #### 2. Get expiry date
    EXPIRY=$(echo "$CERT_INFO" | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)

    if [[ -z "$EXPIRY" ]]; then
        SSL_VALID="INVALID"
        EXPIRY="-"
        DAYS_UNTIL_EXPIRY="NULL"
        EXPIRY_TS="NULL"
    else
        SSL_VALID="VALID"
        
        # Calculate days until expiry
        EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null)
        if [[ -n "$EXPIRY_EPOCH" ]]; then
            NOW_EPOCH=$(date +%s)
            DAYS_UNTIL_EXPIRY=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))
            
            # Convert to PostgreSQL timestamp
            EXPIRY_TS=$(date -d "$EXPIRY" '+%Y-%m-%d %H:%M:%S' 2>/dev/null)
            [[ -z "$EXPIRY_TS" ]] && EXPIRY_TS="NULL"
        else
            DAYS_UNTIL_EXPIRY="NULL"
            EXPIRY_TS="NULL"
        fi
    fi

    #### 3. Check HTTPS status + redirect
    CURL_OUTPUT=$(curl -Ik --max-time $TIMEOUT -L --max-redirs 10 "https://$DOMAIN" 2>/dev/null)

    HTTPS_STATUS=$(echo "$CURL_OUTPUT" | grep -m1 HTTP | awk '{print $2}')
    REDIRECT_TO=$(echo "$CURL_OUTPUT" | grep -i "location:" | tail -n1 | awk '{print $2}' | tr -d '\r')

    [[ -z "$HTTPS_STATUS" ]] && HTTPS_STATUS="NO_RESPONSE"
    [[ -z "$REDIRECT_TO" ]] && REDIRECT_TO="-"

    #### 4. Output result
    echo "RESULT:$DOMAIN_ID|$SSL_VALID|$EXPIRY|$DAYS_UNTIL_EXPIRY|$HTTPS_STATUS|$REDIRECT_TO|$EXPIRY_TS"
}

export -f check_domain
export TIMEOUT

#############################################################################
# Wait for PostgreSQL
#############################################################################
wait_for_db() {
    log_info "Waiting for PostgreSQL to be ready..."
    
    for i in {1..30}; do
        if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" >/dev/null 2>&1; then
            log_info "PostgreSQL is ready!"
            return 0
        fi
        log_warn "PostgreSQL not ready, waiting... ($i/30)"
        sleep 2
    done
    
    log_error "PostgreSQL failed to start after 60 seconds"
    return 1
}

#############################################################################
# Perform scan
#############################################################################
perform_scan() {
    local SCAN_START=$(date +%s)
    
    log_info "=========================================="
    log_info "Starting SSL Certificate Scan"
    log_info "=========================================="
    
    # Refresh materialized view
    psql_query "REFRESH MATERIALIZED VIEW latest_ssl_status;" >/dev/null
    
    # Get active domains
    DOMAIN_LIST=$(psql_query "SELECT id, domain FROM domains WHERE is_active = TRUE ORDER BY domain;")
    
    if [[ -z "$DOMAIN_LIST" ]]; then
        log_warn "No active domains to scan"
        return
    fi
    
    TOTAL_DOMAINS=$(echo "$DOMAIN_LIST" | wc -l)
    log_info "Total domains to scan: $TOTAL_DOMAINS"
    log_info "Concurrency: $CONCURRENCY threads"
    log_info "Timeout: ${TIMEOUT}s per domain"
    log_info ""
    
    # Create temporary files
    TEMP_INPUT=$(mktemp)
    TEMP_OUTPUT=$(mktemp)
    
    # Prepare input
    echo "$DOMAIN_LIST" | while IFS='|' read -r ID DOMAIN; do
        echo "$DOMAIN $ID"
    done > "$TEMP_INPUT"
    
    # Scan all domains in parallel
    log_info "Scanning domains..."
    cat "$TEMP_INPUT" | xargs -P $CONCURRENCY -I {} bash -c 'check_domain $(echo {} | cut -d" " -f1) $(echo {} | cut -d" " -f2)' > "$TEMP_OUTPUT"
    
    # Parse results and insert into database
    log_info "Saving results to database..."
    
    local VALID_COUNT=0
    local INVALID_COUNT=0
    local EXPIRED_SOON=0
    local FAILED_COUNT=0
    
    while IFS='|' read -r PREFIX DOMAIN_ID SSL_STATUS EXPIRY DAYS_UNTIL_EXPIRY HTTPS_STATUS REDIRECT_URL EXPIRY_TS; do
        [[ "$PREFIX" != "RESULT:"* ]] && continue
        
        DOMAIN_ID=$(echo "$PREFIX" | cut -d: -f2)
        
        # Clean up values for SQL
        [[ "$REDIRECT_URL" == "-" ]] && REDIRECT_URL="NULL" || REDIRECT_URL="'$(echo "$REDIRECT_URL" | sed "s/'/''/g")'"
        [[ "$EXPIRY" == "-" ]] && EXPIRY="NULL" || EXPIRY="'$(echo "$EXPIRY" | sed "s/'/''/g")'"
        [[ "$EXPIRY_TS" == "NULL" ]] && EXPIRY_TS="NULL" || EXPIRY_TS="'$EXPIRY_TS'"
        [[ "$DAYS_UNTIL_EXPIRY" == "NULL" ]] && DAYS_UNTIL_EXPIRY="NULL"
        
        # Insert into database
        psql_query "
            INSERT INTO ssl_scan_results
            (domain_id, ssl_status, ssl_expiry_date, days_until_expiry, https_status, redirect_url, ssl_expiry_timestamp)
            VALUES
            ($DOMAIN_ID, '$SSL_STATUS', $EXPIRY, $DAYS_UNTIL_EXPIRY, '$HTTPS_STATUS', $REDIRECT_URL, $EXPIRY_TS);

            UPDATE domains
            SET last_scanned_at = NOW()
            WHERE id = $DOMAIN_ID;
        " >/dev/null 2>&1
        
        # Update counters
        [[ "$SSL_STATUS" == "VALID" ]] && ((VALID_COUNT++))
        [[ "$SSL_STATUS" == "INVALID" ]] && ((INVALID_COUNT++))
        [[ "$HTTPS_STATUS" == "NO_RESPONSE" ]] && ((FAILED_COUNT++))
        
        if [[ "$DAYS_UNTIL_EXPIRY" != "NULL" ]] && [[ $DAYS_UNTIL_EXPIRY -lt 7 ]]; then
            ((EXPIRED_SOON++))
        fi
        
    done < "$TEMP_OUTPUT"
    
    # Refresh materialized view after scan
    psql_query "REFRESH MATERIALIZED VIEW latest_ssl_status;" >/dev/null
    
    # Calculate duration
    SCAN_END=$(date +%s)
    DURATION=$((SCAN_END - SCAN_START))
    
    # Save statistics
    psql_query "
        INSERT INTO scan_stats 
        (total_domains, ssl_valid_count, ssl_invalid_count, expired_soon_count, failed_count, scan_duration_seconds)
        VALUES 
        ($TOTAL_DOMAINS, $VALID_COUNT, $INVALID_COUNT, $EXPIRED_SOON, $FAILED_COUNT, $DURATION);
    " >/dev/null 2>&1
    
    # Cleanup
    rm -f "$TEMP_INPUT" "$TEMP_OUTPUT"
    
    # Print summary
    log_info "=========================================="
    log_info "Scan Completed!"
    log_info "=========================================="
    log_info "Total scanned: $TOTAL_DOMAINS domains"
    log_info "SSL Valid: $VALID_COUNT"
    log_info "SSL Invalid: $INVALID_COUNT"
    log_info "Expired Soon (<7 days): $EXPIRED_SOON"
    log_info "Failed: $FAILED_COUNT"
    log_info "Duration: ${DURATION}s ($(($DURATION / 60))m)"
    
    if [[ $DURATION -gt 0 ]]; then
        THROUGHPUT=$(echo "scale=1; $TOTAL_DOMAINS / $DURATION" | bc)
        log_info "Throughput: ${THROUGHPUT} domains/second"
    fi
    
    log_info "=========================================="
    log_info ""
}

#############################################################################
# Main loop
#############################################################################
main() {
    log_info "SSL Certificate Scanner starting..."
    log_info "Configuration:"
    log_info "  - Database: $DB_HOST:$DB_PORT/$DB_NAME"
    log_info "  - Concurrency: $CONCURRENCY"
    log_info "  - Timeout: ${TIMEOUT}s"
    log_info "  - Scan interval: ${SCAN_INTERVAL}s ($(($SCAN_INTERVAL / 60)) minutes)"
    log_info ""
    
    # Wait for database
    wait_for_db || exit 1
    
    # Main scan loop
    while true; do
        perform_scan
        
        log_info "Sleeping for ${SCAN_INTERVAL}s ($(($SCAN_INTERVAL / 60)) minutes)..."
        log_info ""
        
        sleep $SCAN_INTERVAL
    done
}

# Run
main
