"""
MCP Server implementation that serves tools based on OpenAPI specs, using the fastmcp library.
"""
import json
import logging
from typing import Any, Dict, List, Optional

import yaml
from fastapi import HTTPException  # Kept for ToolExecutor
from starlette.middleware import Middleware  # Added
from starlette.middleware.cors import CORSMiddleware  # Added

from openapi2mcp.auth import OAuthHandler
from openapi2mcp.openapi_parser import OpenAPIParser
from openapi2mcp.tool_executor import ToolExecutor
from fastmcp import FastMCP  # Changed from fastmcp.server import FastMCPServer

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server implementation that serves tools based on OpenAPI specs, using FastMCP."""

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
        self.tools: List[Dict[str, Any]] = []
        self.auth_handler = OAuthHandler(auth_config) if auth_config else None
        self.cors_origins = cors_origins  # Store for use in get_app

        # Parse OpenAPI specs and extract tools
        for spec_file in spec_files:
            self._load_spec(spec_file)  # This populates self.tools

        # Initialize tool executor
        self.tool_executor = ToolExecutor(self.tools, self.auth_handler)

        # Instantiate FastMCP
        # The FastMCP constructor in docs is simple: FastMCP(name="...").
        # It's assumed here that it can be configured with tools and an executor,
        # or that tools can be added to it post-init. This is a key assumption.
        # For now, we'll create it and assume tools/executor are linked via FastMCP's mechanisms.
        self.mcp_instance = FastMCP(
            name="OpenAPI2MCP Server"
            # title, description, version are not standard FastMCP constructor args per docs.
            # These would typically be part of the server's self-description if queried.
        )

        for tool in self.tools:
            self.mcp_instance.add_tool(self.tool_executor.get_tool_function_for_registration(tool["name"]), 
                                       name=tool["name"],
                                       description=tool.get("description")
                                    )
        # Authentication handler might also need to be registered with mcp_instance
        if self.auth_handler and hasattr(self.mcp_instance, "set_auth_handler"):  # Hypothetical
            self.mcp_instance.set_auth_handler(self.auth_handler)

        logger.info("MCPServer initialized with FastMCP.")

    def _load_spec(self, spec_file: str):
        """
        Load an OpenAPI specification file and parse it to extract tools.
        This method populates self.tools.

        Args:
            spec_file: Path to the OpenAPI specification file
        """
        try:
            if spec_file.endswith((".yaml", ".yml")):
                with open(spec_file, "r", encoding="utf-8") as f:
                    spec = yaml.safe_load(f)
            else:  # Assume JSON
                with open(spec_file, "r", encoding="utf-8") as f:
                    spec = json.load(f)

            parser = OpenAPIParser(spec)
            new_tools = parser.extract_tools()
            logger.info(f"Extracted {len(new_tools)} tools from {spec_file}")
            self.tools.extend(new_tools)

        except Exception as e:
            logger.error(f"Failed to load OpenAPI spec from {spec_file}: {str(e)}")
            raise

    def get_app(self):
        """Get the ASGI application instance from FastMCP, with CORS middleware."""

        # Define CORS middleware based on documentation pattern
        cors_middleware = Middleware(
            CORSMiddleware,
            allow_origins=self.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # The http_app() method is used to get the Starlette ASGI app
        # It can take a list of middleware.
        if not hasattr(self.mcp_instance, "http_app"):
            logger.error("The FastMCP instance does not have an 'http_app' method as expected.")
            raise NotImplementedError("FastMCP instance cannot be converted to an ASGI app without 'http_app'.")

        # Pass other necessary configurations if http_app supports them
        # For example, the tool_executor might be passed here if not set earlier,
        # or if http_app is where the server components are finalized.
        # This depends heavily on the actual FastMCP API.
        # For now, assuming http_app primarily deals with transport and middleware.

        # The documentation for FastMCP.http_app shows it can take 'middleware'.
        # It also shows it can take 'path' and 'transport'.
        # We'll assume the tools and executor are already configured on self.mcp_instance.

        return self.mcp_instance.http_app(middleware=[cors_middleware])
