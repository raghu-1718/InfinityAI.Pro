"""
Celery worker startup script for InfinityAI.Pro
Entry point for running Celery worker processes
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir.parent))

from app.tasks import celery_app, init_celery_db, close_celery_db
import structlog

logger = structlog.get_logger(__name__)

def main():
    """Main entry point for Celery worker"""
    try:
        # Initialize database pool for worker
        logger.info("Initializing Celery worker database pool")
        init_celery_db()
        
        # Start the worker
        logger.info("Starting Celery worker")
        celery_app.worker_main([
            'worker',
            '--loglevel=info',
            '--concurrency=4',
            '--queues=broker_validation,maintenance,trading,celery',
            '--hostname=infinityai-worker@%h'
        ])
        
    except KeyboardInterrupt:
        logger.info("Celery worker stopping...")
    except Exception as e:
        logger.error("Celery worker failed", error=str(e))
        raise
    finally:
        # Clean up database pool
        close_celery_db()
        logger.info("Celery worker stopped")

if __name__ == '__main__':
    main()