"""
Scanner main entry point
"""
import asyncio
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import scanner
try:
    from scanner import SSLScanner
except ImportError:
    logger.error("❌ Failed to import SSLScanner")
    sys.exit(1)

async def main():
    """Main function"""
    logger.info("🚀 Starting SSL Monitor Scanner")
    
    scanner = SSLScanner()
    
    try:
        await scanner.run()
    except KeyboardInterrupt:
        logger.info("⏸️ Scanner stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())