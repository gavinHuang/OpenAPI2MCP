"""
Tests for the tool executor.
"""
import json
import unittest
from unittest.mock import patch, MagicMock

import aiohttp
from aiohttp.client_reqrep import ClientResponse

from openapi2mcp.tool_executor import ToolExecutor

class TestToolExecutor(unittest.TestCase):
    """Tests for the ToolExecutor class."""
    
    def setUp(self):
        """Set up test data."""
        self.sample_tools = [
            {
                "name": "getUsers",
                "description": "Get all users",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of users to return"
                        }
                    }
                },
                "openapi_metadata": {
                    "path": "/users",
                    "method": "get",
                    "base_url": "https://api.example.com/v1"
                }
            },
            {
                "name": "getUserById",
                "description": "Get user by ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "userId": {
                            "type": "string",
                            "description": "ID of the user to retrieve"
                        }
                    },
                    "required": ["userId"]
                },
                "openapi_metadata": {
                    "path": "/users/{userId}",
                    "method": "get",
                    "base_url": "https://api.example.com/v1"
                }
            },
            {
                "name": "createUser",
                "description": "Create a new user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the user"
                        },
                        "email": {
                            "type": "string",
                            "description": "Email address of the user"
                        }
                    },
                    "required": ["name", "email"]
                },
                "openapi_metadata": {
                    "path": "/users",
                    "method": "post",
                    "base_url": "https://api.example.com/v1"
                }
            }
        ]
        
        self.executor = ToolExecutor(self.sample_tools)
    
    @patch("aiohttp.ClientSession.get")
    async def test_execute_get_tool(self, mock_get):
        """Test execution of a GET tool."""
        # Configure the mock
        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = MagicMock(return_value={"users": [{"id": 1, "name": "John Doe"}]})
        mock_response.headers = {"Content-Type": "application/json"}
        
        # Use context manager to return the mock response
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Execute the tool
        result = await self.executor.execute_tool("getUsers", {"limit": 10})
        
        # Check that the result is as expected
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["data"]["users"][0]["name"], "John Doe")
        
        # Check that the get method was called with the correct URL and parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["limit"], 10)
    
    @patch("aiohttp.ClientSession.get")
    async def test_execute_path_parameter_tool(self, mock_get):
        """Test execution of a tool with path parameters."""
        # Configure the mock
        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = MagicMock(return_value={"id": "user123", "name": "John Doe"})
        mock_response.headers = {"Content-Type": "application/json"}
        
        # Use context manager to return the mock response
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Execute the tool
        result = await self.executor.execute_tool("getUserById", {"userId": "user123"})
        
        # Check that the result is as expected
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["data"]["name"], "John Doe")
        
        # Check that the get method was called with the correct URL (with path parameter substituted)
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertTrue("https://api.example.com/v1/users/user123" in str(args))
    
    @patch("aiohttp.ClientSession.post")
    async def test_execute_post_tool(self, mock_post):
        """Test execution of a POST tool."""
        # Configure the mock
        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 201
        mock_response.json = MagicMock(return_value={"id": "new-user", "name": "Jane Doe", "email": "jane@example.com"})
        mock_response.headers = {"Content-Type": "application/json"}
        
        # Use context manager to return the mock response
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Execute the tool
        result = await self.executor.execute_tool("createUser", {
            "name": "Jane Doe",
            "email": "jane@example.com"
        })
        
        # Check that the result is as expected
        self.assertEqual(result["status_code"], 201)
        self.assertEqual(result["data"]["name"], "Jane Doe")
        
        # Check that the post method was called with the correct data
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["name"], "Jane Doe")
        self.assertEqual(kwargs["json"]["email"], "jane@example.com")
    
    async def test_tool_not_found(self):
        """Test that an error is raised when a tool is not found."""
        with self.assertRaises(ValueError):
            await self.executor.execute_tool("nonExistentTool", {})

if __name__ == "__main__":
    unittest.main()
