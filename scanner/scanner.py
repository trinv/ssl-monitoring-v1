"""
SSL Certificate Scanner Module
Handles SSL certificate scanning with retry logic and error handling
"""
import asyncio
import logging
import os
import socket
import ssl
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncpg
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import backoff
from enum import Enum

# ============================================
# Configuration
# ============================================
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "ssl_monitor")
DB_USER = os.getenv("DB_USER", "ssluser")
DB_PASSWORD = os.getenv("DB_PASSWORD")

CONCURRENCY = int(os.getenv("SCANNER_CONCURRENCY", "20"))
TIMEOUT = int(os.getenv("SCANNER_TIMEOUT", "15"))
RETRY = int(os.getenv("SCANNER_RETRY", "3"))
BATCH_SIZE = int(os.getenv("SCANNER_BATCH_SIZE", "1000"))
VERIFY_SSL = os.getenv("SCANNER_VERIFY_SSL", "false").lower() == "true"

# ============================================
# Enums
# ============================================
class ScanStatus(str, Enum):
    """Scan status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

# ============================================
# SSL Scanner Class
# ============================================
class SSLScanner:
    """SSL Certificate Scanner"""
    
    def __init__(self):
        """Initialize scanner"""
        self.db_pool: Optional[asyncpg.Pool] = None
        self.semaphore = asyncio.Semaphore(CONCURRENCY)
        
        logger.info(f"🚀 Scanner initialized - Concurrency: {CONCURRENCY}, Timeout: {TIMEOUT}s")
    
    # ============================================
    # Database Connection
    # ============================================
    async def connect_db(self):
        """Create database connection pool"""
        try:
            self.db_pool = await asyncpg.create_pool(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                min_size=5,
                max_size=20,
                command_timeout=30,
                connection_class=asyncpg.connect,
                init=self._init_connection  # ✅ Add initialization
            )
            logger.info("✅ Database connected")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {str(e)}")
            raise
        
    async def _init_connection(self, conn):
        """Initialize connection"""
        await conn.set_type_codec(
            'json',
            encoder=json.dumps,
            decoder=json.loads,
            schema='pg_catalog'
        )

    async def disconnect_db(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("✅ Database disconnected")
    

    # ============================================
    # SSL Certificate Scanning with Retry Logic
    # ============================================
    @backoff.on_exception(
        backoff.expo,
        (socket.error, ssl.SSLError, TimeoutError),
        max_tries=RETRY,
        max_time=60,
        base=2
    )
    async def get_ssl_certificate(
        self,
        domain: str,
        port: int = 443
    ) -> Dict:
        """
        Get SSL certificate from domain with exponential backoff retry
        
        Args:
            domain: Domain name
            port: Port number (default: 443)
            
        Returns:
            Certificate information dictionary
            
        Raises:
            socket.error: Connection error
            ssl.SSLError: SSL error
            TimeoutError: Timeout
        """
        try:
            # ============================================
            # Create SSL Context
            # ============================================
            context = ssl.create_default_context()

            if not VERIFY_SSL:
                # Disable SSL verification for monitoring purposes
                # We're just checking certificate existence and expiry
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            else:
                # Full SSL verification enabled
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
            
            # ============================================
            # Connect and Get Certificate
            # ============================================
            with socket.create_connection((domain, port), timeout=TIMEOUT) as sock:
                # Set socket timeout explicitly
                sock.settimeout(TIMEOUT)
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    # Get DER certificate
                    der_cert = ssock.getpeercert(binary_form=True)
                    
                    if not der_cert:
                        logger.warning(f"⚠️ No certificate found for {domain}")
                        return {"status": "failed", "error": "No certificate found"}
                    
                    # Parse certificate
                    cert = x509.load_der_x509_certificate(
                        der_cert,
                        default_backend()
                    )
                    
                    # ============================================
                    # Extract Certificate Information
                    # ============================================
                    cert_info = {
                        "domain": domain,
                        "common_name": cert.subject.get_attributes_for_oid(
                            x509.oid.NameOID.COMMON_NAME
                        )[0].value if cert.subject.get_attributes_for_oid(
                            x509.oid.NameOID.COMMON_NAME
                        ) else None,
                        "subject_alt_names": self._extract_san(cert),
                        "issuer": str(cert.issuer),
                        "serial_number": str(cert.serial_number),
                        "issued_date": cert.not_valid_before.isoformat(),
                        "expiry_date": cert.not_valid_after.isoformat(),
                        "is_self_signed": cert.issuer == cert.subject,
                        "key_size": cert.public_key().key_size,
                        "signature_algorithm": str(cert.signature_algorithm_oid),
                        "is_valid": self._is_certificate_valid(cert),
                        "days_until_expiry": (
                            cert.not_valid_after - datetime.utcnow()
                        ).days,
                        "scanned_at": datetime.utcnow().isoformat(),
                        "status": "success"
                    }
                    
                    logger.info(f"✅ Certificate scanned: {domain}")
                    return cert_info
                    
        except socket.timeout:
            logger.warning(f"⏱️ Timeout scanning {domain}")
            raise TimeoutError(f"Timeout connecting to {domain}")
        except ssl.SSLError as e:
            logger.warning(f"🔒 SSL Error scanning {domain}: {str(e)}")
            raise
        except socket.error as e:
            logger.warning(f"🌐 Connection error scanning {domain}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error scanning {domain}: {str(e)}")
            return {
                "domain": domain,
                "status": "failed",
                "error": str(e)
            }
    
    # ============================================
    # Certificate Validation
    # ============================================
    def _is_certificate_valid(self, cert) -> bool:
        """Check if certificate is valid"""
        try:
            now = datetime.utcnow()
            return cert.not_valid_before <= now <= cert.not_valid_after
        except:
            return False
    
    def _extract_san(self, cert) -> List[str]:
        """Extract Subject Alternative Names"""
        try:
            san_ext = cert.extensions.get_extension_for_oid(
                x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
            )
            return [name.value for name in san_ext.value]
        except:
            return []
    
    # ============================================
    # Database Operations
    # ============================================
    async def save_scan_result(
        self,
        domain_id: int,
        cert_info: Dict
    ) -> bool:
        """
        Save scan result to database
        
        Args:
            domain_id: Domain ID
            cert_info: Certificate information
            
        Returns:
            True if saved, False otherwise
        """
        if not self.db_pool:
            logger.error("❌ Database not connected")
            return False
        
        try:
            async with self.db_pool.acquire() as conn:
                # ============================================
                # Save Scan Result
                # ============================================
                await conn.execute(
                    """
                    INSERT INTO scan_results
                    (domain_id, scan_type, status, result_data, started_at, completed_at)
                    VALUES ($1, $2, $3, $4, NOW(), NOW())
                    """,
                    domain_id,
                    "ssl",
                    cert_info.get("status", "failed"),
                    json.dumps(cert_info)
                )
                
                # ============================================
                # Update Domain Last Scanned
                # ============================================
                if cert_info.get("status") == "success":
                    await conn.execute(
                        """
                        UPDATE domains 
                        SET last_scanned = NOW()
                        WHERE id = $1
                        """,
                        domain_id
                    )
                    
                    # ============================================
                    # Save Certificate
                    # ============================================
                    await conn.execute(
                        """
                        INSERT INTO ssl_certificates 
                        (domain_id, common_name, subject_alt_names, issuer, 
                         serial_number, issued_date, expiry_date, is_self_signed, 
                         key_size, signature_algorithm, scanned_at, is_valid)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), $11)
                        ON CONFLICT (domain_id) DO UPDATE SET
                            expiry_date = EXCLUDED.expiry_date,
                            is_valid = EXCLUDED.is_valid,
                            scanned_at = NOW()
                        """,
                        domain_id,
                        cert_info.get("common_name"),
                        str(cert_info.get("subject_alt_names", [])),
                        cert_info.get("issuer"),
                        cert_info.get("serial_number"),
                        cert_info.get("issued_date"),
                        cert_info.get("expiry_date"),
                        cert_info.get("is_self_signed"),
                        cert_info.get("key_size"),
                        cert_info.get("signature_algorithm"),
                        cert_info.get("is_valid")
                    )
                    
                    logger.info(f"✅ Scan result saved for domain_id: {domain_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to save scan result: {str(e)}")
            return False
    
    # ============================================
    # Batch Scanning
    # ============================================
    async def scan_domain(self, domain_id: int, domain_name: str) -> Dict:
        """
        Scan single domain with concurrency control
        
        Args:
            domain_id: Domain ID
            domain_name: Domain name
            
        Returns:
            Scan result
        """
        async with self.semaphore:
            try:
                cert_info = await self.get_ssl_certificate(domain_name)
                
                # Save to database
                await self.save_scan_result(domain_id, cert_info)
                
                return {
                    "domain_id": domain_id,
                    "domain_name": domain_name,
                    "result": cert_info
                }
                
            except Exception as e:
                logger.error(f"❌ Failed to scan {domain_name}: {str(e)}")
                return {
                    "domain_id": domain_id,
                    "domain_name": domain_name,
                    "result": {
                        "status": "failed",
                        "error": str(e)
                    }
                }
    
    async def scan_batch(self, domains: List[Tuple[int, str]]) -> List[Dict]:
        """
        Scan batch of domains with concurrency control
        
        Args:
            domains: List of (domain_id, domain_name) tuples
            
        Returns:
            List of scan results
        """
        logger.info(f"🚀 Starting batch scan of {len(domains)} domains")
        
        tasks = [
            self.scan_domain(domain_id, domain_name)
            for domain_id, domain_name in domains
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if isinstance(r, dict) and r["result"]["status"] == "success")
        failed = len(results) - successful
        
        logger.info(f"✅ Batch scan completed - Success: {successful}, Failed: {failed}")
        
        return results
    
    # ============================================
    # Get Domains to Scan
    # ============================================
    async def get_domains_to_scan(self) -> List[Tuple[int, str]]:
        """
        Get active domains that need scanning
        
        Returns:
            List of (domain_id, domain_name) tuples
        """
        if not self.db_pool:
            logger.error("❌ Database not connected")
            return []
        
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, domain_name FROM domains 
                    WHERE is_active = true
                    ORDER BY last_scanned ASC NULLS FIRST
                    LIMIT $1
                    """,
                    BATCH_SIZE
                )
                
                return [(row["id"], row["domain_name"]) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Failed to get domains: {str(e)}")
            return []
    
    # ============================================
    # Main Scanner Loop
    # ============================================
    async def run(self):
        """Main scanner loop"""
        try:
            await self.connect_db()
            
            while True:
                try:
                    # Get domains to scan
                    domains = await self.get_domains_to_scan()
                    
                    if not domains:
                        logger.info("⏳ No domains to scan, waiting...")
                        await asyncio.sleep(60)
                        continue
                    
                    # Scan batch
                    await self.scan_batch(domains)
                    
                    # Wait before next batch
                    await asyncio.sleep(30)
                    
                except Exception as e:
                    logger.error(f"❌ Scanner error: {str(e)}")
                    await asyncio.sleep(60)
                    
        except Exception as e:
            logger.error(f"❌ Fatal error: {str(e)}")
        finally:
            await self.disconnect_db()