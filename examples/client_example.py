"""
Sample client script demonstrating how to use the MCP server.
"""
import asyncio
import json
import requests
from pprint import pprint

async def main():
    # MCP server URL
    mcp_url = "http://127.0.0.1:8000/mcp"
    
    # Get MCP info
    print("Getting MCP server info...")
    response = requests.get(mcp_url)
    pprint(response.json())
    
    # Get available tools
    print("\nGetting available tools...")
    response = requests.get(f"{mcp_url}/tools")
    tools = response.json()["tools"]
    
    # Print available tools
    print(f"\nFound {len(tools)} MCP tools:")
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool['name']} - {tool.get('description', '').split('\n')[0]}")
    
    # Execute the "getUsers" tool
    print("\nExecuting 'getUsers' tool...")
    tool_data = {
        "name": "getUsers",
        "parameters": {
            "limit": 5
        }
    }
    
    response = requests.post(f"{mcp_url}/run", json=tool_data)
    result = response.json()
    
    print("\nTool execution result:")
    pprint(result)

if __name__ == "__main__":
    asyncio.run(main())
