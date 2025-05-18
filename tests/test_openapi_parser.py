"""
Tests for OpenAPI2MCP.
"""
import json
import os
import tempfile
import unittest

from openapi2mcp.openapi_parser import OpenAPIParser

class TestOpenAPIParser(unittest.TestCase):
    """Tests for the OpenAPIParser class."""
    
    def setUp(self):
        """Set up test data."""
        self.sample_spec = {
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
                    },
                    "post": {
                        "summary": "Create a user",
                        "operationId": "createUser",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {
                                                "type": "string"
                                            },
                                            "email": {
                                                "type": "string"
                                            }
                                        },
                                        "required": ["name", "email"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "Created"
                            }
                        }
                    }
                },
                "/users/{userId}": {
                    "get": {
                        "summary": "Get user by ID",
                        "operationId": "getUserById",
                        "parameters": [
                            {
                                "name": "userId",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "string"
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
        }
    
    def test_extract_base_url(self):
        """Test that the base URL is correctly extracted from the OpenAPI spec."""
        parser = OpenAPIParser(self.sample_spec)
        self.assertEqual(parser._extract_base_url(), "https://api.example.com/v1")
    
    def test_generate_tool_name(self):
        """Test that tool names are correctly generated from paths and methods."""
        parser = OpenAPIParser(self.sample_spec)
        
        self.assertEqual(
            parser._generate_tool_name("/users", "get"),
            "getUsers"
        )
        
        self.assertEqual(
            parser._generate_tool_name("/users/{userId}", "get"),
            "getUsersUserId"
        )
    
    def test_extract_tools(self):
        """Test that tools are correctly extracted from the OpenAPI spec."""
        parser = OpenAPIParser(self.sample_spec)
        tools = parser.extract_tools()
        
        # Check that we extracted the expected number of tools
        self.assertEqual(len(tools), 3)
        
        # Check that the tools have the expected names
        tool_names = [tool["name"] for tool in tools]
        self.assertIn("getUsers", tool_names)
        self.assertIn("postUsers", tool_names)
        self.assertIn("getUsersUserId", tool_names)
        
        # Check that the GET /users tool has the expected parameters
        get_users_tool = next(tool for tool in tools if tool["name"] == "getUsers")
        self.assertIn("limit", get_users_tool["parameters"]["properties"])
        
        # Check that the POST /users tool has the expected parameters
        post_users_tool = next(tool for tool in tools if tool["name"] == "postUsers")
        self.assertIn("name", post_users_tool["parameters"]["properties"])
        self.assertIn("email", post_users_tool["parameters"]["properties"])
        self.assertIn("name", post_users_tool["parameters"]["required"])
        self.assertIn("email", post_users_tool["parameters"]["required"])
        
        # Check that the GET /users/{userId} tool has the expected parameters
        get_user_tool = next(tool for tool in tools if tool["name"] == "getUsersUserId")
        self.assertIn("userId", get_user_tool["parameters"]["properties"])
        self.assertIn("userId", get_user_tool["parameters"]["required"])

if __name__ == "__main__":
    unittest.main()
