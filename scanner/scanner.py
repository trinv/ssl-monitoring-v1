"""
SSL Certificate Scanner
Optimized for high concurrency
Based on bash check_ssl_bulk.sh logic
"""

import asyncio
import asyncpg
import ssl
import socket
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import os
import logging

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ssluser:SSL@Pass123@postgres:5432/ssl_monitor")
SCAN_CONCURRENCY = int(os.getenv("SCAN_CONCURRENCY", "2000"))
SCAN_TIMEOUT = int(os.getenv("SCAN_TIMEOUT", "10"))
SCHEDULE_INTERVAL = int(os.getenv("SCHEDULE_INTERVAL", "3600"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "5000"))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_ssl_certificate(domain: str, timeout: int = 10) -> Optional[Dict]:
    """
    Get SSL certificate information for a domain
    Equivalent to: openssl s_client -connect domain:443
    """
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Create socket connection with timeout
        sock = socket.create_connection((domain, 443), timeout=timeout)
        ssock = context.wrap_socket(sock, server_hostname=domain)
        
        # Get certificate
        cert = ssock.getpeercert()
        
        if not cert:
            ssock.close()
            return None
        
        # Parse expiry date
        expiry_str = cert.get('notAfter')
        if expiry_str:
            # Parse date format: 'Nov 26 12:00:00 2025 GMT'
            expiry_date = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
        else:
            expiry_date = None
        
        # Get issuer and subject
        issuer = dict(x[0] for x in cert.get('issuer', []))
        subject = dict(x[0] for x in cert.get('subject', []))
        
        ssock.close()
        
        return {
            'valid': True,
            'expiry_date': expiry_date,
            'issuer': issuer.get('organizationName', 'Unknown'),
            'subject': subject.get('commonName', domain)
        }
        
    except (socket.timeout, socket.gaierror, ssl.SSLError, ConnectionRefusedError, OSError) as e:
        return None
    except Exception as e:
        logger.error(f"SSL certificate error for {domain}: {e}")
        return None


# Removed HTTPS status check - only focusing on SSL certificate validation


async def scan_domain(domain: str, semaphore: asyncio.Semaphore) -> Dict:
    """
    Scan a single domain for SSL certificate only
    """
    async with semaphore:
        result = {
            'domain': domain,
            'ssl_status': 'INVALID',
            'ssl_expiry_date': None,
            'days_until_expiry': None,
            'error_message': None
        }

        # Check SSL certificate
        ssl_info = await get_ssl_certificate(domain, timeout=SCAN_TIMEOUT)

        if ssl_info and ssl_info.get('valid'):
            result['ssl_status'] = 'VALID'
            result['ssl_expiry_date'] = ssl_info.get('expiry_date')

            # Calculate days until expiry
            if result['ssl_expiry_date']:
                days_diff = (result['ssl_expiry_date'] - datetime.now()).days
                result['days_until_expiry'] = days_diff
        else:
            result['ssl_status'] = 'INVALID'
            result['error_message'] = 'Cannot retrieve SSL certificate'

        return result


async def bulk_insert_results(pool: asyncpg.Pool, results: List[Dict]) -> None:
    """
    Bulk insert scan results into database
    """
    if not results:
        return
    
    async with pool.acquire() as conn:
        # Prepare data for COPY
        records = []
        for r in results:
            # Get domain_id
            domain_id = await conn.fetchval(
                "SELECT id FROM domains WHERE domain = $1",
                r['domain']
            )
            
            if not domain_id:
                continue
            
            # Format ssl_expiry_timestamp
            ssl_expiry_ts = r['ssl_expiry_date'] if r['ssl_expiry_date'] else None

            records.append((
                domain_id,
                datetime.now(),
                r['ssl_status'],
                ssl_expiry_ts,
                r['days_until_expiry'],
                r['error_message']
            ))

        if records:
            # Use COPY for bulk insert (fast!)
            await conn.copy_records_to_table(
                'ssl_scan_results',
                columns=['domain_id', 'scan_time', 'ssl_status', 'ssl_expiry_timestamp',
                        'days_until_expiry', 'error_message'],
                records=records
            )
            
            # Update last_scanned_at
            domain_ids = [r[0] for r in records]
            await conn.execute("""
                UPDATE domains 
                SET last_scanned_at = $1 
                WHERE id = ANY($2::int[])
            """, datetime.now(), domain_ids)


async def perform_scan(pool: asyncpg.Pool) -> None:
    """
    Main scan function
    """
    try:
        logger.info("=" * 80)
        logger.info("Starting SSL Certificate Scan")
        logger.info("=" * 80)
        
        scan_start = datetime.now()
        
        # Get active domains
        async with pool.acquire() as conn:
            domains = await conn.fetch("""
                SELECT domain FROM domains WHERE is_active = TRUE ORDER BY domain
            """)
        
        total_domains = len(domains)
        
        if total_domains == 0:
            logger.warning("No active domains to scan")
            return
        
        logger.info(f"Total domains to scan: {total_domains:,}")
        logger.info(f"Concurrency: {SCAN_CONCURRENCY:,}")
        logger.info(f"Batch size: {BATCH_SIZE:,}")
        logger.info(f"Timeout: {SCAN_TIMEOUT}s")
        logger.info("")
        
        # Process in batches
        total_scanned = 0
        summary = {
            'ssl_valid': 0,
            'ssl_invalid': 0,
            'expired_soon': 0,
            'failed': 0
        }
        
        domain_list = [d['domain'] for d in domains]

        # Create semaphore
        semaphore = asyncio.Semaphore(SCAN_CONCURRENCY)

        for offset in range(0, total_domains, BATCH_SIZE):
            batch_start = datetime.now()
            batch = domain_list[offset:offset + BATCH_SIZE]

            logger.info(f"Processing batch: {offset:,}-{min(offset + BATCH_SIZE, total_domains):,} of {total_domains:,}")

            # Scan batch
            tasks = [scan_domain(domain, semaphore) for domain in batch]
            batch_results = await asyncio.gather(*tasks)

            # Insert results
            await bulk_insert_results(pool, batch_results)

            # Update summary
            for result in batch_results:
                if result['ssl_status'] == 'VALID':
                    summary['ssl_valid'] += 1
                    if result['days_until_expiry'] and result['days_until_expiry'] < 7:
                        summary['expired_soon'] += 1
                else:
                    summary['ssl_invalid'] += 1

            total_scanned += len(batch)
            batch_duration = (datetime.now() - batch_start).total_seconds()

            logger.info(f"Batch completed in {batch_duration:.1f}s - Valid: {summary['ssl_valid']}, Invalid: {summary['ssl_invalid']}")
            logger.info("")
        
        # Refresh materialized view
        async with pool.acquire() as conn:
            await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY latest_ssl_status")
        
        scan_duration = int((datetime.now() - scan_start).total_seconds())
        
        # Record statistics
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO scan_stats
                (scan_time, total_domains, ssl_valid_count, ssl_invalid_count,
                 expired_soon_count, scan_duration_seconds)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, datetime.now(), total_scanned, summary['ssl_valid'],
            summary['ssl_invalid'], summary['expired_soon'], scan_duration)
        
        logger.info("=" * 80)
        logger.info("Scan Completed Successfully!")
        logger.info(f"Total scanned: {total_scanned:,} domains")
        logger.info(f"SSL Valid: {summary['ssl_valid']:,}")
        logger.info(f"SSL Invalid: {summary['ssl_invalid']:,}")
        logger.info(f"Expired Soon: {summary['expired_soon']:,}")
        
        if scan_duration > 0:
            logger.info(f"Total duration: {scan_duration}s ({scan_duration/60:.1f} minutes)")
            logger.info(f"Throughput: {total_scanned/scan_duration:.1f} domains/second")
        else:
            logger.info(f"Total duration: <1s (very fast)")
        
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during scan: {e}", exc_info=True)


async def main():
    """
    Main entry point
    """
    # Wait for database to be ready (retry logic)
    logger.info("Waiting for PostgreSQL to be ready...")
    pool = None
    max_retries = 30
    retry_delay = 2

    for attempt in range(1, max_retries + 1):
        try:
            pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=10,
                max_size=50,
                command_timeout=60
            )
            logger.info("✅ Connected to database")
            break
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"PostgreSQL not ready (attempt {attempt}/{max_retries}), retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to PostgreSQL after {max_retries} attempts: {e}")
                raise

    if not pool:
        raise Exception("Failed to create database pool")

    TRIGGER_FILE = "/tmp/ssl_scan_trigger"

    while True:
        try:
            await perform_scan(pool)

            logger.info(f"💤 Sleeping for {SCHEDULE_INTERVAL}s ({SCHEDULE_INTERVAL/60:.0f} minutes)")
            logger.info("You can trigger immediate scan via API endpoint: POST /api/scan/trigger")
            logger.info("")

            # Sleep with periodic checks for trigger file (check every 10 seconds)
            sleep_interval = 10
            elapsed = 0

            while elapsed < SCHEDULE_INTERVAL:
                # Check if trigger file exists
                if os.path.exists(TRIGGER_FILE):
                    logger.info("⚡ Scan trigger detected! Starting immediate scan...")
                    os.remove(TRIGGER_FILE)
                    break

                await asyncio.sleep(sleep_interval)
                elapsed += sleep_interval
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            await asyncio.sleep(60)
    
    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
