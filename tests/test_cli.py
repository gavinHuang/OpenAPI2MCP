"""
Tests for the CLI module.
"""
import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from openapi2mcp.cli import parse_args, extract_tools_from_specs

class TestCLI(unittest.TestCase):
    """Tests for the CLI module."""
    
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
    
    def test_parse_args_serve(self):
        """Test parsing 'serve' command arguments."""
        args = parse_args(["serve", "--spec-file", self.spec_file, "--port", "9000"])
        
        self.assertEqual(args.command, "serve")
        self.assertEqual(args.spec_file, [self.spec_file])
        self.assertEqual(args.port, 9000)
    
    def test_parse_args_convert(self):
        """Test parsing 'convert' command arguments."""
        output_file = os.path.join(self.temp_dir.name, "tools.json")
        args = parse_args(["convert", "--spec-file", self.spec_file, "--output", output_file])
        
        self.assertEqual(args.command, "convert")
        self.assertEqual(args.spec_file, [self.spec_file])
        self.assertEqual(args.output, output_file)
    
    def test_extract_tools_from_specs(self):
        """Test extracting tools from specification files."""
        tools = extract_tools_from_specs([self.spec_file])
        
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "getUsers")
        self.assertEqual(tools[0]["openapi_metadata"]["method"], "get")
        self.assertEqual(tools[0]["openapi_metadata"]["path"], "/users")
    
    @patch("openapi2mcp.cli.serve_command")
    def test_main_serve(self, mock_serve):
        """Test main function with 'serve' command."""
        with patch("sys.argv", ["openapi2mcp", "serve", "--spec-file", self.spec_file]):
            from openapi2mcp.cli import main
            main()
            
            mock_serve.assert_called_once()
    
    @patch("openapi2mcp.cli.convert_command")
    def test_main_convert(self, mock_convert):
        """Test main function with 'convert' command."""
        output_file = os.path.join(self.temp_dir.name, "tools.json")
        with patch("sys.argv", ["openapi2mcp", "convert", "--spec-file", self.spec_file, "--output", output_file]):
            from openapi2mcp.cli import main
            main()
            
            mock_convert.assert_called_once()

if __name__ == "__main__":
    unittest.main()
