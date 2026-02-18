"""
Background scheduler worker for dashboard data refresh.
This runs as a separate thread/process to update data every 30 minutes.
"""

import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler = None
_scheduler_started = False
_lock = None

def init_scheduler(data_callback, lock=None):
    """
    Initialize the background scheduler.
    
    Args:
        data_callback: Function to call for data refresh
        lock: Optional threading lock for thread-safe operations
    """
    global _scheduler, _scheduler_started, _lock
    
    if _scheduler_started:
        logger.warning("Scheduler already initialized")
        return _scheduler
    
    _lock = lock
    _scheduler = BackgroundScheduler(daemon=True)
    
    # Add job to refresh data every 30 minutes
    _scheduler.add_job(
        func=_refresh_job,
        args=(data_callback,),
        trigger="interval",
        minutes=30,
        id="refresh_dashboard_data",
        name="Refresh dashboard data every 30 minutes",
        max_instances=1  # Prevent concurrent executions
    )
    
    # Also run immediately on startup
    _scheduler.add_job(
        func=_refresh_job,
        args=(data_callback,),
        id="initial_refresh",
        name="Initial data refresh on startup"
    )
    
    _scheduler.start()
    _scheduler_started = True
    
    # Graceful shutdown
    atexit.register(lambda: _scheduler.shutdown() if _scheduler else None)
    
    logger.info("✅ Scheduler started: Data will refresh every 30 minutes")
    return _scheduler

def _refresh_job(data_callback):
    """Internal job function that handles data refresh"""
    try:
        logger.info("🔄 Starting data refresh job...")
        if _lock:
            with _lock:
                data_callback()
        else:
            data_callback()
        logger.info("✅ Data refresh completed successfully")
    except Exception as e:
        logger.error(f"❌ Error during data refresh: {e}", exc_info=True)

def stop_scheduler():
    """Stop the scheduler gracefully"""
    global _scheduler, _scheduler_started
    
    if _scheduler and _scheduler_started:
        try:
            _scheduler.shutdown()
            _scheduler_started = False
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
