"""
Tests for the OAuth authentication handler.
"""
import os
import unittest
from unittest.mock import patch, MagicMock

from openapi2mcp.auth import OAuthHandler

class TestOAuthHandler(unittest.TestCase):
    """Tests for the OAuthHandler class."""
    
    def setUp(self):
        """Set up test data."""
        self.test_config = {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "token_url": "https://api.example.com/oauth/token"
        }
    
    def test_init_with_config(self):
        """Test initialization with explicit config."""
        handler = OAuthHandler(self.test_config)
        
        self.assertEqual(handler.client_id, "test-client-id")
        self.assertEqual(handler.client_secret, "test-client-secret")
        self.assertEqual(handler.token_url, "https://api.example.com/oauth/token")
    
    @patch.dict(os.environ, {
        "API_CLIENT_ID": "env-client-id",
        "API_CLIENT_SECRET": "env-client-secret",
        "API_TOKEN_URL": "https://api.example.com/env/token"
    })
    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        handler = OAuthHandler()
        
        self.assertEqual(handler.client_id, "env-client-id")
        self.assertEqual(handler.client_secret, "env-client-secret")
        self.assertEqual(handler.token_url, "https://api.example.com/env/token")
    
    @patch("requests.post")
    async def test_refresh_token(self, mock_post):
        """Test token refresh functionality."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test-access-token",
            "expires_in": 3600
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Create handler and refresh token
        handler = OAuthHandler(self.test_config)
        token = await handler.refresh_token()
        
        # Check that the token was refreshed correctly
        self.assertEqual(token, "test-access-token")
        self.assertEqual(handler.token_info["access_token"], "test-access-token")
        
        # Check that the requests.post method was called with the correct arguments
        mock_post.assert_called_once_with(
            "https://api.example.com/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "test-client-id",
                "client_secret": "test-client-secret"
            }
        )
    
    @patch("openapi2mcp.auth.OAuthHandler.get_access_token")
    async def test_add_auth_to_request(self, mock_get_token):
        """Test that authentication is correctly added to request headers."""
        # Configure the mock
        mock_get_token.return_value = "test-access-token"
        
        # Create handler and add auth to headers
        handler = OAuthHandler(self.test_config)
        headers = await handler.add_auth_to_request({})
        
        # Check that the Authorization header was added
        self.assertEqual(headers["Authorization"], "Bearer test-access-token")
        
        # Check that get_access_token was called
        mock_get_token.assert_called_once()

if __name__ == "__main__":
    unittest.main()
