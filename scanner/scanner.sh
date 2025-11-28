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
        echo "RESULT:$DOMAIN_ID|INVALID|NULL|NULL"
        return
    fi

    #### 2. Get expiry date
    EXPIRY=$(echo "$CERT_INFO" | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)

    if [[ -z "$EXPIRY" ]]; then
        SSL_VALID="INVALID"
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

    #### 3. Output result
    echo "RESULT:$DOMAIN_ID|$SSL_VALID|$DAYS_UNTIL_EXPIRY|$EXPIRY_TS"
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
# Perform scan (full or selective)
#############################################################################
perform_scan() {
    local SCAN_START=$(date +%s)
    local SCAN_REQUEST_FILE="$1"

    log_info "=========================================="
    if [[ -n "$SCAN_REQUEST_FILE" ]]; then
        log_info "Starting Selective SSL Certificate Scan"
    else
        log_info "Starting Full SSL Certificate Scan"
    fi
    log_info "=========================================="

    # Refresh materialized view
    psql_query "REFRESH MATERIALIZED VIEW latest_ssl_status;" >/dev/null

    # Get domains to scan
    if [[ -n "$SCAN_REQUEST_FILE" ]] && [[ -f "$SCAN_REQUEST_FILE" ]]; then
        # Selective scan - read from file
        DOMAIN_LIST=$(cat "$SCAN_REQUEST_FILE")
        log_info "Selective scan requested"
    else
        # Full scan - get all active domains from database
        DOMAIN_LIST=$(psql_query "SELECT id, domain FROM domains WHERE is_active = TRUE ORDER BY domain;")
    fi

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
    
    while IFS='|' read -r PREFIX SSL_STATUS DAYS_UNTIL_EXPIRY EXPIRY_TS; do
        [[ "$PREFIX" != "RESULT:"* ]] && continue

        DOMAIN_ID=$(echo "$PREFIX" | cut -d: -f2)

        # Clean up values for SQL
        [[ "$EXPIRY_TS" == "NULL" ]] && EXPIRY_TS="NULL" || EXPIRY_TS="'$EXPIRY_TS'"
        [[ "$DAYS_UNTIL_EXPIRY" == "NULL" ]] && DAYS_UNTIL_EXPIRY="NULL"

        # Insert into database
        psql_query "
            INSERT INTO ssl_scan_results
            (domain_id, ssl_status, ssl_expiry_timestamp, days_until_expiry)
            VALUES
            ($DOMAIN_ID, '$SSL_STATUS', $EXPIRY_TS, $DAYS_UNTIL_EXPIRY);

            UPDATE domains
            SET last_scanned_at = NOW()
            WHERE id = $DOMAIN_ID;
        " >/dev/null 2>&1

        # Update counters
        [[ "$SSL_STATUS" == "VALID" ]] && ((VALID_COUNT++))
        [[ "$SSL_STATUS" == "INVALID" ]] && ((INVALID_COUNT++))
        
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
        (total_domains, ssl_valid_count, ssl_invalid_count, expired_soon_count, scan_duration_seconds)
        VALUES
        ($TOTAL_DOMAINS, $VALID_COUNT, $INVALID_COUNT, $EXPIRED_SOON, $DURATION);
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
    log_info "Duration: ${DURATION}s ($(($DURATION / 60))m)"
    
    if [[ $DURATION -gt 0 ]]; then
        THROUGHPUT=$(echo "scale=1; $TOTAL_DOMAINS / $DURATION" | bc)
        log_info "Throughput: ${THROUGHPUT} domains/second"
    fi
    
    log_info "=========================================="
    log_info ""
}

#############################################################################
# Calculate seconds until next 00:00 UTC
#############################################################################
seconds_until_midnight_utc() {
    local NOW_UTC=$(date -u +%s)
    local TODAY_MIDNIGHT=$(date -u -d "today 00:00:00" +%s)
    local TOMORROW_MIDNIGHT=$(date -u -d "tomorrow 00:00:00" +%s)

    if [ $NOW_UTC -lt $TODAY_MIDNIGHT ]; then
        echo $((TODAY_MIDNIGHT - NOW_UTC))
    else
        echo $((TOMORROW_MIDNIGHT - NOW_UTC))
    fi
}

#############################################################################
# Main loop - Scan once per day at 00:00 UTC
#############################################################################
main() {
    log_info "SSL Certificate Scanner starting..."
    log_info "Configuration:"
    log_info "  - Database: $DB_HOST:$DB_PORT/$DB_NAME"
    log_info "  - Concurrency: $CONCURRENCY"
    log_info "  - Timeout: ${TIMEOUT}s"
    log_info "  - Schedule: Daily at 00:00 UTC"
    log_info ""

    # Wait for database
    wait_for_db || exit 1

    # Check if we should run initial scan
    LAST_SCAN_FILE="/tmp/last_scan_date"
    TODAY_UTC=$(date -u +%Y-%m-%d)

    if [ -f "$LAST_SCAN_FILE" ]; then
        LAST_SCAN_DATE=$(cat "$LAST_SCAN_FILE")
        if [ "$LAST_SCAN_DATE" != "$TODAY_UTC" ]; then
            log_info "No scan performed today yet. Running initial scan..."
            perform_scan
            echo "$TODAY_UTC" > "$LAST_SCAN_FILE"
        else
            log_info "Scan already performed today ($TODAY_UTC). Waiting for next schedule."
        fi
    else
        log_info "First run. Performing initial scan..."
        perform_scan
        echo "$TODAY_UTC" > "$LAST_SCAN_FILE"
    fi

    # Main loop - wait until 00:00 UTC each day
    TRIGGER_FILE="/tmp/ssl_scan_trigger"

    while true; do
        SECONDS_TO_WAIT=$(seconds_until_midnight_utc)
        NEXT_SCAN_TIME=$(date -u -d "tomorrow 00:00:00" '+%Y-%m-%d %H:%M:%S UTC')

        log_info "Next scheduled scan: $NEXT_SCAN_TIME"
        log_info "Waiting for ${SECONDS_TO_WAIT}s ($(($SECONDS_TO_WAIT / 3600))h $(($SECONDS_TO_WAIT % 3600 / 60))m)"
        log_info "You can trigger immediate scan via API endpoint: POST /api/scan/trigger"
        log_info ""

        # Sleep with periodic checks for trigger file (check every 5 seconds)
        SLEEP_INTERVAL=5
        ELAPSED=0

        while [ $ELAPSED -lt $SECONDS_TO_WAIT ]; do
            # Check if trigger file exists
            if [ -f "$TRIGGER_FILE" ]; then
                TRIGGER_CONTENT=$(cat "$TRIGGER_FILE")
                rm -f "$TRIGGER_FILE"

                # Check if it's a selective scan (file path) or full scan (timestamp)
                if [[ -f "$TRIGGER_CONTENT" ]]; then
                    log_info "⚡ Selective scan trigger detected! Scanning specific domains..."
                    perform_scan "$TRIGGER_CONTENT"
                    rm -f "$TRIGGER_CONTENT"
                else
                    log_info "⚡ Full scan trigger detected! Starting immediate full scan..."
                    perform_scan
                    TODAY_UTC=$(date -u +%Y-%m-%d)
                    echo "$TODAY_UTC" > "$LAST_SCAN_FILE"
                fi
                break
            fi

            sleep $SLEEP_INTERVAL
            ELAPSED=$((ELAPSED + SLEEP_INTERVAL))
        done

        # If we reached midnight (no manual trigger), perform scheduled scan
        if [ $ELAPSED -ge $SECONDS_TO_WAIT ]; then
            log_info "⏰ Scheduled scan time reached (00:00 UTC). Starting full scan..."
            perform_scan
            TODAY_UTC=$(date -u +%Y-%m-%d)
            echo "$TODAY_UTC" > "$LAST_SCAN_FILE"
        fi
    done
}

# Run
main
