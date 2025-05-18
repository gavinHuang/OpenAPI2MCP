"""
OAuth authentication handler for API requests.
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class OAuthHandler:
    """OAuth authentication handler for API requests."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the OAuth handler.
        
        Args:
            config: OAuth configuration (default: None, uses environment variables)
        """
        self.config = config or {}
        self.token_info = None
        self.token_expiry = None
        
        # Load configuration from environment variables if not provided
        self.client_id = self.config.get("client_id") or os.getenv("API_CLIENT_ID")
        self.client_secret = self.config.get("client_secret") or os.getenv("API_CLIENT_SECRET")
        self.token_url = self.config.get("token_url") or os.getenv("API_TOKEN_URL")
        
        # Validate required configuration
        if not all([self.client_id, self.client_secret, self.token_url]):
            logger.warning(
                "OAuth configuration incomplete. Ensure client_id, client_secret, and token_url are provided "
                "either in config or as environment variables."
            )
    
    async def get_access_token(self) -> Optional[str]:
        """
        Get a valid OAuth access token, refreshing if necessary.
        
        Returns:
            Access token string or None if authentication fails
        """
        # Check if we have a valid token
        if self.token_info and self.token_expiry and self.token_expiry > datetime.now():
            return self.token_info.get("access_token")
        
        # If not, request a new token
        return await self.refresh_token()
    
    async def refresh_token(self) -> Optional[str]:
        """
        Refresh the OAuth token.
        
        Returns:
            New access token string or None if refresh fails
        """
        if not all([self.client_id, self.client_secret, self.token_url]):
            logger.error("Cannot refresh token: OAuth configuration incomplete")
            return None
        
        try:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            self.token_info = response.json()
            
            # Calculate token expiry time (default to 3600 seconds if not specified)
            expires_in = self.token_info.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)  # Refresh 60 seconds early
            
            logger.info("OAuth token refreshed successfully")
            return self.token_info.get("access_token")
            
        except Exception as e:
            logger.error(f"Failed to refresh OAuth token: {str(e)}")
            return None
    
    async def add_auth_to_request(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Add authentication to request headers.
        
        Args:
            headers: Existing request headers
            
        Returns:
            Updated headers with authentication
        """
        token = await self.get_access_token()
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        return headers
