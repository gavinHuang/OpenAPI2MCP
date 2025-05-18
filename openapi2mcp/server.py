"""
MCP Server implementation that serves tools based on OpenAPI specs.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
import asyncio

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from openapi2mcp.auth import OAuthHandler
from openapi2mcp.openapi_parser import OpenAPIParser
from openapi2mcp.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)

class MCPServer:
    """MCP Server implementation that serves tools based on OpenAPI specs."""
    
    def __init__(
        self,
        spec_files: List[str],
        auth_config: Optional[Dict[str, Any]] = None,
        cors_origins: List[str] = ["*"],
    ):
        """
        Initialize the MCP server with OpenAPI specifications.
        
        Args:
            spec_files: List of paths to OpenAPI specification files
            auth_config: Authentication configuration (default: None)
            cors_origins: List of allowed CORS origins (default: ["*"])
        """
        self.app = FastAPI(title="OpenAPI2MCP Server")
        self.tools = []
        self.resources = {}
        self.prompts = {}
        self.auth_handler = OAuthHandler(auth_config) if auth_config else None
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Parse OpenAPI specs and extract tools
        for spec_file in spec_files:
            self._load_spec(spec_file)
            
        # Set up MCP routes
        self._setup_routes()
        
        # Initialize tool executor
        self.tool_executor = ToolExecutor(self.tools, self.auth_handler)
    
    def _load_spec(self, spec_file: str):
        """
        Load an OpenAPI specification file and parse it to extract tools.
        
        Args:
            spec_file: Path to the OpenAPI specification file
        """
        try:
            if spec_file.endswith(('.yaml', '.yml')):
                with open(spec_file, 'r') as f:
                    spec = yaml.safe_load(f)
            else:  # Assume JSON
                with open(spec_file, 'r') as f:
                    spec = json.load(f)
                    
            parser = OpenAPIParser(spec)
            new_tools = parser.extract_tools()
            logger.info(f"Extracted {len(new_tools)} tools from {spec_file}")
            self.tools.extend(new_tools)
            
        except Exception as e:
            logger.error(f"Failed to load OpenAPI spec from {spec_file}: {str(e)}")
            raise
    
    def _setup_routes(self):
        """Set up the MCP server routes."""
        
        @self.app.get("/mcp")
        async def get_mcp_info():
            """Get MCP server information."""
            return {
                "name": "OpenAPI2MCP Server",
                "version": "0.1.0",
                "supports": {
                    "tools": True,
                    "resources": False,
                    "prompts": False
                }
            }
        
        @self.app.get("/mcp/tools")
        async def get_tools():
            """Get all available tools."""
            return {"tools": self.tools}
        
        @self.app.post("/mcp/run")
        async def run_tool(request: Request):
            """Run a tool and return the result."""
            data = await request.json()
            tool_name = data.get("name")
            params = data.get("parameters", {})
            
            result = await self.tool_executor.execute_tool(tool_name, params)
            return {"result": result}
        
        @self.app.get("/mcp/sse")
        async def sse_endpoint(request: Request):
            """Server-Sent Events endpoint for streaming tool execution."""
            async def event_generator():
                # Send initial connection established event
                yield {"event": "connected", "data": json.dumps({"status": "connected"})}
                
                # Keep the connection open until client disconnects
                while True:
                    if await request.is_disconnected():
                        break
                    
                    # Wait for tool execution requests
                    # This is simplified for now - in a real implementation
                    # we would need a queue or similar mechanism
                    await asyncio.sleep(1)
            
            return EventSourceResponse(event_generator())

    def get_app(self):
        """Get the FastAPI application instance."""
        return self.app
