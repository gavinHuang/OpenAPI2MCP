"""
Tool executor for running MCP tools against the OpenAPI endpoints.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp

from openapi2mcp.auth import OAuthHandler

logger = logging.getLogger(__name__)

class ToolExecutor:
    """Tool executor for running MCP tools against the OpenAPI endpoints."""
    
    def __init__(self, tools: List[Dict[str, Any]], auth_handler: Optional[OAuthHandler] = None):
        """
        Initialize the tool executor.
        
        Args:
            tools: List of MCP tools
            auth_handler: OAuth authentication handler (default: None)
        """
        self.tools = {tool["name"]: tool for tool in tools}
        self.auth_handler = auth_handler
    
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with the given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            params: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If the tool is not found
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        metadata = tool.get("openapi_metadata", {})
        
        method = metadata.get("method", "get").lower()
        path = metadata.get("path", "")
        base_url = metadata.get("base_url", "")
        
        # Replace path parameters in the URL
        url = base_url + path
        for param_name, param_value in params.items():
            url = url.replace(f"{{{param_name}}}", str(param_value))
        
        # Set up headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Add authentication if available
        if self.auth_handler:
            headers = await self.auth_handler.add_auth_to_request(headers)
        
        # Prepare request data
        request_data = {}
        for param_name, param_value in params.items():
            # Skip path parameters that have already been used
            if f"{{{param_name}}}" not in path:
                request_data[param_name] = param_value
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "get":
                    async with session.get(url, headers=headers, params=request_data) as response:
                        return await self._process_response(response)
                        
                elif method == "post":
                    async with session.post(url, headers=headers, json=request_data) as response:
                        return await self._process_response(response)
                        
                elif method == "put":
                    async with session.put(url, headers=headers, json=request_data) as response:
                        return await self._process_response(response)
                        
                elif method == "delete":
                    async with session.delete(url, headers=headers, params=request_data) as response:
                        return await self._process_response(response)
                        
                elif method == "patch":
                    async with session.patch(url, headers=headers, json=request_data) as response:
                        return await self._process_response(response)
                        
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                    
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {str(e)}")
            return {"error": str(e)}
    
    async def _process_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """
        Process an HTTP response.
        
        Args:
            response: HTTP response object
            
        Returns:
            Processed response data
        """
        status_code = response.status
        
        try:
            # Try to parse response as JSON
            data = await response.json()
            
        except json.JSONDecodeError:
            # If not JSON, return text
            data = {"text": await response.text()}
        
        return {
            "status_code": status_code,
            "data": data,
            "headers": dict(response.headers)
        }
