"""
Example script demonstrating how to use OpenAPI2MCP programmatically.
"""
import argparse
import asyncio
import json
import os
import sys
from typing import Dict, Any, List

import uvicorn
import yaml
from dotenv import load_dotenv

from openapi2mcp.auth import OAuthHandler
from openapi2mcp.openapi_parser import OpenAPIParser
from openapi2mcp.server import MCPServer

# Load environment variables from .env file
load_dotenv()

async def list_tools_from_spec(spec_file: str) -> List[Dict[str, Any]]:
    """
    Extract and print tools from an OpenAPI specification file.
    
    Args:
        spec_file: Path to the OpenAPI specification file
        
    Returns:
        List of tools extracted from the specification
    """
    print(f"Loading OpenAPI specification from {spec_file}...")
    
    # Load the OpenAPI specification
    if spec_file.endswith(('.yaml', '.yml')):
        with open(spec_file, 'r') as f:
            spec = yaml.safe_load(f)
    else:  # Assume JSON
        with open(spec_file, 'r') as f:
            spec = json.load(f)
    
    # Extract tools from the specification
    parser = OpenAPIParser(spec)
    tools = parser.extract_tools()
    
    print(f"Extracted {len(tools)} tools from the specification.\n")
    print("Available tools:")
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool['name']} - {tool.get('description', '').split('\n')[0]}")
    
    return tools

async def run_mcp_server(spec_file: str, host: str = "127.0.0.1", port: int = 8000) -> None:
    """
    Run an MCP server with tools from an OpenAPI specification file.
    
    Args:
        spec_file: Path to the OpenAPI specification file
        host: Host to run the server on (default: 127.0.0.1)
        port: Port to run the server on (default: 8000)
    """
    print(f"Starting MCP server with specification from {spec_file}...")
    
    # Load authentication configuration from environment variables
    auth_config = {
        "client_id": os.environ.get("API_CLIENT_ID"),
        "client_secret": os.environ.get("API_CLIENT_SECRET"),
        "token_url": os.environ.get("API_TOKEN_URL")
    }
    
    # Create an OAuth handler if all required config is present
    auth_handler = None
    if all(auth_config.values()):
        auth_handler = OAuthHandler(auth_config)
        print("OAuth authentication configured.")
    else:
        print("OAuth authentication not configured. Set API_CLIENT_ID, API_CLIENT_SECRET, and API_TOKEN_URL environment variables to enable.")
    
    # Create and start the MCP server
    server = MCPServer(spec_files=[spec_file], auth_config=auth_config if auth_handler else None)
    app = server.get_app()
    
    # Show information about the server
    print(f"\nMCP server ready at http://{host}:{port}/mcp")
    print(f"Available endpoints:")
    print(f"- GET  /mcp              - Get server information")
    print(f"- GET  /mcp/tools        - Get available tools")
    print(f"- POST /mcp/run          - Run a tool")
    print(f"- GET  /mcp/sse          - Server-Sent Events endpoint")
    
    # Show example tool usage
    if server.tools:
        print(f"\nExample tool usage (first tool):")
        tool = server.tools[0]
        parameters = {}
        for param_name, param_schema in tool.get("parameters", {}).get("properties", {}).items():
            # Generate a sample value for each parameter
            if param_schema.get("type") == "string":
                if "enum" in param_schema:
                    parameters[param_name] = param_schema["enum"][0]
                else:
                    parameters[param_name] = f"sample_{param_name}"
            elif param_schema.get("type") == "integer":
                parameters[param_name] = 10
            elif param_schema.get("type") == "boolean":
                parameters[param_name] = True
        
        print(f"curl -X POST http://{host}:{port}/mcp/run \\")
        print(f"  -H \"Content-Type: application/json\" \\")
        print(f"  -d '{{")
        print(f'    "name": "{tool["name"]}",')
        print(f'    "parameters": {json.dumps(parameters, indent=6)}')
        print(f"  }}'")
    
    print("\nPress Ctrl+C to stop the server.")
    
    # Run the server
    uvicorn.run(app, host=host, port=port)

async def export_tools_to_json(spec_file: str, output_file: str) -> None:
    """
    Export tools from an OpenAPI specification file to a JSON file.
    
    Args:
        spec_file: Path to the OpenAPI specification file
        output_file: Path to the output JSON file
    """
    print(f"Exporting tools from {spec_file} to {output_file}...")
    
    # Extract tools from the specification
    tools = await list_tools_from_spec(spec_file)
    
    # Write tools to the output file
    with open(output_file, 'w') as f:
        json.dump({"tools": tools}, f, indent=2)
    
    print(f"Successfully exported {len(tools)} tools to {output_file}.")

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="OpenAPI2MCP Example Script")
    parser.add_argument('--spec-file', '-s', required=True, help='Path to the OpenAPI specification file')
    
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')
    
    # 'list' action
    list_parser = subparsers.add_parser('list', help='List tools from an OpenAPI specification')
    
    # 'serve' action
    serve_parser = subparsers.add_parser('serve', help='Run an MCP server with tools from an OpenAPI specification')
    serve_parser.add_argument('--host', default='127.0.0.1', help='Host to run the server on (default: 127.0.0.1)')
    serve_parser.add_argument('--port', '-p', type=int, default=8000, help='Port to run the server on (default: 8000)')
    
    # 'export' action
    export_parser = subparsers.add_parser('export', help='Export tools from an OpenAPI specification to a JSON file')
    export_parser.add_argument('--output', '-o', required=True, help='Path to the output JSON file')
    
    args = parser.parse_args()
    
    if args.action == 'list':
        await list_tools_from_spec(args.spec_file)
    elif args.action == 'serve':
        await run_mcp_server(args.spec_file, args.host, args.port)
    elif args.action == 'export':
        await export_tools_to_json(args.spec_file, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
