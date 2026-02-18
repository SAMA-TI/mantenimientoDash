"""
Data manager for dashboard with automatic refresh capability.
This module wraps the data loading logic and enables periodic updates.
"""

import threading
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardDataManager:
    """Manages dashboard data with automatic periodic refresh"""
    
    def __init__(self):
        self.data_lock = threading.Lock()
        self.scheduler = None
        self.data = {}
        self.load_callback = None
        
    def register_load_callback(self, callback):
        """Register the function that loads data"""
        self.load_callback = callback
        
    def load_data(self):
        """Load data using the registered callback"""
        if not self.load_callback:
            logger.warning("No load callback registered")
            return
            
        try:
            logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Refreshing dashboard data...")
            with self.data_lock:
                self.data = self.load_callback()
            logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Dashboard data refreshed successfully")
        except Exception as e:
            logger.error(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Error refreshing data: {e}", exc_info=True)
            
    def get_data(self, key=None):
        """Thread-safe data retrieval"""
        with self.data_lock:
            if key:
                return self.data.get(key)
            return self.data.copy()
            
    def start_scheduler(self, interval_minutes=30):
        """Start the background scheduler for periodic updates"""
        if self.scheduler:
            logger.warning("Scheduler already running")
            return
            
        # Initial load
        self.load_data()
        
        # Setup scheduler
        self.scheduler = BackgroundScheduler(daemon=True)
        self.scheduler.add_job(
            func=self.load_data,
            trigger="interval",
            minutes=interval_minutes,
            id="dashboard_refresh",
            max_instances=1
        )
        self.scheduler.start()
        atexit.register(self._shutdown)
        
        logger.info(f"✅ Scheduler started: Data will refresh every {interval_minutes} minutes")
        
    def _shutdown(self):
        """Gracefully stop the scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

# Global instance
data_manager = DashboardDataManager()
