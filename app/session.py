"""
In-memory session management module
"""
import logging
from typing import Dict, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages user session state in memory
    Sessions auto-expire after 30 minutes of inactivity
    """
    
    def __init__(self, ttl_minutes: int = 30):
        """
        Initialize session manager
        
        Args:
            ttl_minutes: Session TTL in minutes (default 30)
        """
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def set_state(
        self, 
        user_id: str, 
        stage: str, 
        selected_amount: Optional[Decimal]
    ) -> None:
        """
        Set session state for user
        
        Args:
            user_id: LINE user ID
            stage: Current stage ('awaiting_amount' or 'awaiting_people')
            selected_amount: Selected amount (None for awaiting_amount stage)
        """
        with self._lock:
            self._sessions[user_id] = {
                'stage': stage,
                'selected_amount': selected_amount,
                'last_activity': datetime.now()
            }
            logger.debug(f"Session set for user {user_id}: stage={stage}")
    
    def get_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session state for user
        
        Args:
            user_id: LINE user ID
            
        Returns:
            Session state dict or None if no session/expired
        """
        with self._lock:
            if user_id not in self._sessions:
                return None
            
            session = self._sessions[user_id]
            
            # Check if session expired
            if datetime.now() - session['last_activity'] > self.ttl:
                del self._sessions[user_id]
                logger.debug(f"Session expired for user {user_id}")
                return None
            
            # Update last activity
            session['last_activity'] = datetime.now()
            
            return {
                'stage': session['stage'],
                'selected_amount': session['selected_amount']
            }
    
    def clear_state(self, user_id: str) -> None:
        """
        Clear session state for user
        
        Args:
            user_id: LINE user ID
        """
        with self._lock:
            if user_id in self._sessions:
                del self._sessions[user_id]
                logger.debug(f"Session cleared for user {user_id}")
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired sessions
        
        Returns:
            Number of sessions removed
        """
        with self._lock:
            now = datetime.now()
            expired_users = [
                user_id for user_id, session in self._sessions.items()
                if now - session['last_activity'] > self.ttl
            ]
            
            for user_id in expired_users:
                del self._sessions[user_id]
            
            if expired_users:
                logger.info(f"Cleaned up {len(expired_users)} expired sessions")
            
            return len(expired_users)