"""
Usage tracking module for free tier management
"""
import logging
from datetime import datetime
from threading import Lock
from zoneinfo import ZoneInfo
from typing import Optional

logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Tracks monthly OCR usage to enforce free tier limits
    Automatically resets counter at month boundaries
    """
    
    def __init__(
        self, 
        timezone: str = "Asia/Tokyo",
        monthly_cap: int = 1000,
        free_mode: bool = True
    ):
        """
        Initialize usage tracker
        
        Args:
            timezone: Timezone for month boundary calculation
            monthly_cap: Monthly OCR call limit
            free_mode: Whether to enforce free tier limits
        """
        self.timezone = timezone
        self.monthly_cap = monthly_cap
        self.free_mode = free_mode
        self._lock = Lock()
        
        # Initialize counter
        self._current_month_key = self._get_month_key()
        self._counter = 0
        
        logger.info(
            f"Usage tracker initialized: timezone={timezone}, "
            f"cap={monthly_cap}, free_mode={free_mode}"
        )
    
    def _get_month_key(self) -> str:
        """
        Get current month key (YYYY-MM format)
        
        Returns:
            Month key string
        """
        try:
            tz = ZoneInfo(self.timezone)
            now = datetime.now(tz)
        except:
            # Fallback to UTC if timezone is invalid
            now = datetime.utcnow()
            logger.warning(f"Invalid timezone {self.timezone}, using UTC")
        
        return now.strftime("%Y-%m")
    
    def _check_month_reset(self) -> None:
        """Check if month has changed and reset counter if needed"""
        current_key = self._get_month_key()
        
        if current_key != self._current_month_key:
            self._current_month_key = current_key
            self._counter = 0
            logger.info(f"Month changed to {current_key}, counter reset")
    
    def increment(self) -> int:
        """
        Increment usage counter and return new count
        
        Returns:
            Updated counter value
        """
        with self._lock:
            self._check_month_reset()
            self._counter += 1
            logger.debug(f"Usage incremented to {self._counter}/{self.monthly_cap}")
            return self._counter
    
    def get_current_count(self) -> int:
        """
        Get current usage count
        
        Returns:
            Current counter value
        """
        with self._lock:
            self._check_month_reset()
            return self._counter
    
    def is_limit_exceeded(self) -> bool:
        """
        Check if monthly limit has been exceeded
        
        Returns:
            True if limit exceeded and free_mode is enabled
        """
        if not self.free_mode:
            return False
        
        with self._lock:
            self._check_month_reset()
            exceeded = self._counter >= self.monthly_cap
            
            if exceeded:
                logger.warning(
                    f"Monthly limit exceeded: {self._counter}/{self.monthly_cap}"
                )
            
            return exceeded
    
    def get_remaining(self) -> Optional[int]:
        """
        Get remaining usage count for the month
        
        Returns:
            Remaining count or None if free_mode is disabled
        """
        if not self.free_mode:
            return None
        
        with self._lock:
            self._check_month_reset()
            return max(0, self.monthly_cap - self._counter)
    
    def reset(self) -> None:
        """Force reset the counter (for testing/admin purposes)"""
        with self._lock:
            self._counter = 0
            logger.info("Usage counter manually reset")