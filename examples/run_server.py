"""
Sample script demonstrating how to use OpenAPI2MCP.
"""
import os
import json
import asyncio
from openapi2mcp.server import MCPServer
import uvicorn

async def main():
    # Path to OpenAPI specification file
    spec_file = os.path.join(os.path.dirname(__file__), "sample_api.yaml")
    
    # Create MCP server
    server = MCPServer(spec_files=[spec_file])
    
    # Get tools
    tools = server.tools
    
    # Print available tools
    print(f"Generated {len(tools)} MCP tools:")
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool['name']} - {tool.get('description', '').split('\n')[0]}")
    
    # Run the server
    app = server.get_app()
    
    # Start the server
    print("\nStarting MCP server on http://127.0.0.1:8000")
    print("Press Ctrl+C to stop")
    
    # Run the server (this will block)
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    asyncio.run(main())
