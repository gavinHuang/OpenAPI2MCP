"""
Command-line interface for OpenAPI2MCP.
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from typing import List

import uvicorn
import yaml

from openapi2mcp.openapi_parser import OpenAPIParser
from openapi2mcp.server import MCPServer

logger = logging.getLogger(__name__)

def setup_logging(level: str = "INFO"):
    """Set up logging configuration."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()]
    )

def parse_args(args: List[str]):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="OpenAPI2MCP - Convert OpenAPI specs to MCP server with tools")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # "serve" command
    serve_parser = subparsers.add_parser("serve", help="Start an MCP server with tools from OpenAPI specs")
    serve_parser.add_argument("--spec-file", "-s", required=True, action="append",
                             help="Path to OpenAPI specification file(s) (JSON or YAML)")
    serve_parser.add_argument("--port", "-p", type=int, default=8000,
                             help="Port to run the server on (default: 8000)")
    serve_parser.add_argument("--host", default="127.0.0.1",
                             help="Host to run the server on (default: 127.0.0.1)")
    
    # "convert" command
    convert_parser = subparsers.add_parser("convert", help="Convert OpenAPI specs to MCP tools JSON")
    convert_parser.add_argument("--spec-file", "-s", required=True, action="append",
                               help="Path to OpenAPI specification file(s) (JSON or YAML)")
    convert_parser.add_argument("--output", "-o", required=True,
                               help="Output file path for MCP tools JSON")
    
    # Common arguments
    for subparser in [serve_parser, convert_parser]:
        subparser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                              default="INFO", help="Set the logging level")
    
    return parser.parse_args(args)

def load_auth_config():
    """Load authentication configuration from environment variables."""
    auth_config = {
        "client_id": os.environ.get("API_CLIENT_ID"),
        "client_secret": os.environ.get("API_CLIENT_SECRET"),
        "token_url": os.environ.get("API_TOKEN_URL")
    }
    
    # Only return the config if all required values are present
    if all(auth_config.values()):
        return auth_config
    
    # Log warning about missing auth config
    missing = [k for k, v in auth_config.items() if not v]
    if missing:
        logger.warning(f"Missing authentication configuration: {', '.join(missing)}")
        logger.warning("OAuth authentication will not be available.")
    
    return None

def extract_tools_from_specs(spec_files: List[str]):
    """Extract MCP tools from OpenAPI specification files."""
    all_tools = []
    
    for spec_file in spec_files:
        try:
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
            all_tools.extend(tools)
            
            logger.info(f"Extracted {len(tools)} tools from {spec_file}")
            
        except Exception as e:
            logger.error(f"Failed to extract tools from {spec_file}: {str(e)}")
            raise
    
    return all_tools

def serve_command(args):
    """Run the MCP server."""
    logger.info(f"Starting OpenAPI2MCP server with {len(args.spec_file)} OpenAPI spec(s)")
    
    # Load authentication configuration
    auth_config = load_auth_config()
    
    # Create MCP server
    server = MCPServer(spec_files=args.spec_file, auth_config=auth_config)
    
    # Print available tools
    logger.info("Available tools:")
    if server.tools:
        for i, tool in enumerate(server.tools, 1):
            tool_name = tool.get('name', 'Unnamed tool')
            tool_description = tool.get('description', 'No description').split('\n')[0]
            logger.info(f"{i}. {tool_name} - {tool_description}")
    else:
        logger.info("No tools available.")

    # Run the server
    app = server.get_app()
    
    # Convert to sync function for uvicorn
    uvicorn.run(app, host=args.host, port=args.port)

async def convert_command(args):
    """Convert OpenAPI specs to MCP tools JSON."""
    logger.info(f"Converting {len(args.spec_file)} OpenAPI spec(s) to MCP tools")
    
    # Extract tools from specifications
    tools = extract_tools_from_specs(args.spec_file)
    
    # Write tools to output file
    with open(args.output, 'w') as f:
        json.dump({"tools": tools}, f, indent=2)
    
    logger.info(f"Wrote {len(tools)} tools to {args.output}")

def main():
    """Main entry point for the OpenAPI2MCP CLI."""
    args = parse_args(sys.argv[1:])
    setup_logging(args.log_level)
    
    if args.command == "serve":
        # asyncio.run(serve_command(args)) # Changed: Call directly
        serve_command(args)
    elif args.command == "convert":
        asyncio.run(convert_command(args))
    else:
        logger.error("No command specified. Use 'serve' or 'convert'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
