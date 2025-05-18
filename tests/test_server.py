"""
Tests for the MCP server.
"""
import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from openapi2mcp.server import MCPServer

class TestMCPServer(unittest.TestCase):
    """Tests for the MCPServer class."""
    
    def setUp(self):
        """Set up test data."""
        # Create a temporary OpenAPI spec file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.spec_file = os.path.join(self.temp_dir.name, "test_api.json")
        
        with open(self.spec_file, "w") as f:
            json.dump({
                "openapi": "3.0.0",
                "info": {
                    "title": "Test API",
                    "version": "1.0.0"
                },
                "servers": [
                    {
                        "url": "https://api.example.com/v1"
                    }
                ],
                "paths": {
                    "/users": {
                        "get": {
                            "summary": "Get all users",
                            "operationId": "getUsers",
                            "parameters": [
                                {
                                    "name": "limit",
                                    "in": "query",
                                    "schema": {
                                        "type": "integer"
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "OK"
                                }
                            }
                        }
                    }
                }
            }, f)
    
    def tearDown(self):
        """Clean up test data."""
        self.temp_dir.cleanup()
    
    def test_server_initialization(self):
        """Test that the server is correctly initialized with OpenAPI specs."""
        server = MCPServer(spec_files=[self.spec_file])
        
        # Check that the tools were loaded
        self.assertEqual(len(server.tools), 1)
        self.assertEqual(server.tools[0]["name"], "getUsers")
    
    def test_get_mcp_info(self):
        """Test the /mcp endpoint."""
        server = MCPServer(spec_files=[self.spec_file])
        client = TestClient(server.get_app())
        
        response = client.get("/mcp")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "OpenAPI2MCP Server")
        self.assertTrue(response.json()["supports"]["tools"])
    
    def test_get_tools(self):
        """Test the /mcp/tools endpoint."""
        server = MCPServer(spec_files=[self.spec_file])
        client = TestClient(server.get_app())
        
        response = client.get("/mcp/tools")
        
        self.assertEqual(response.status_code, 200)
        tools = response.json()["tools"]
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "getUsers")
    
    @patch("openapi2mcp.tool_executor.ToolExecutor.execute_tool")
    def test_run_tool(self, mock_execute_tool):
        """Test the /mcp/run endpoint."""
        # Configure the mock
        mock_execute_tool.return_value = {"status_code": 200, "data": {"users": []}}
        
        # Create server and test client
        server = MCPServer(spec_files=[self.spec_file])
        client = TestClient(server.get_app())
        
        # Make a request to run a tool
        response = client.post(
            "/mcp/run",
            json={"name": "getUsers", "parameters": {"limit": 10}}
        )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        
        # Check that execute_tool was called with the correct arguments
        mock_execute_tool.assert_called_once_with("getUsers", {"limit": 10})

if __name__ == "__main__":
    unittest.main()
