# OpenAPI2MCP Documentation

## Overview

OpenAPI2MCP is a Python tool that converts OpenAPI specifications into MCP (Model Context Protocol) servers with tools. It allows AI models to interact with APIs defined by OpenAPI specifications through the standardized MCP interface.

## Installation

### From PyPI

```bash
pip install openapi2mcp
```

### From Source

```bash
git clone https://github.com/yourusername/openapi2mcp.git
cd openapi2mcp
pip install -e .
```

## Usage

### Basic Usage

OpenAPI2MCP provides two main commands:

1. `serve` - Start an MCP server with tools from OpenAPI specs
2. `convert` - Convert OpenAPI specs to MCP tools JSON without starting a server

#### Starting an MCP Server

```bash
openapi2mcp serve --spec-file /path/to/openapi.yaml --port 8000
```

This will:
1. Parse the OpenAPI specification from the specified file
2. Extract tools from the specification
3. Start an MCP server on the specified port (default: 8000)

#### Converting OpenAPI Specs to MCP Tools

```bash
openapi2mcp convert --spec-file /path/to/openapi.yaml --output tools.json
```

This will:
1. Parse the OpenAPI specification from the specified file
2. Extract tools from the specification
3. Write the tools to the specified output file in MCP format

### OAuth Authentication

OpenAPI2MCP supports OAuth authentication for API calls. To use OAuth authentication, you need to provide credentials either through environment variables or a configuration file.

#### Environment Variables

Create a `.env` file in your project directory with the following variables:

```
API_CLIENT_ID=your_client_id
API_CLIENT_SECRET=your_client_secret
API_TOKEN_URL=https://example.com/oauth/token
```

Or set them directly in your environment:

```bash
export API_CLIENT_ID=your_client_id
export API_CLIENT_SECRET=your_client_secret
export API_TOKEN_URL=https://example.com/oauth/token
```

#### Configuration File

You can also provide credentials through a configuration file:

```yaml
# auth_config.yaml
client_id: your_client_id
client_secret: your_client_secret
token_url: https://example.com/oauth/token
```

And load it programmatically when creating an MCP server:

```python
import yaml
from openapi2mcp.server import MCPServer

# Load authentication configuration
with open('auth_config.yaml', 'r') as f:
    auth_config = yaml.safe_load(f)

# Create MCP server with authentication
server = MCPServer(spec_files=['openapi.yaml'], auth_config=auth_config)
```

## API Reference

### MCPServer

The `MCPServer` class is the main entry point for creating an MCP server.

```python
from openapi2mcp.server import MCPServer

# Create an MCP server
server = MCPServer(
    spec_files=['path/to/openapi.yaml'],  # List of OpenAPI specification files
    auth_config=None,                     # Optional authentication configuration
    cors_origins=["*"]                    # Optional CORS origins (default: ["*"])
)

# Get the FastAPI application instance
app = server.get_app()

# Run the server with uvicorn
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8000)
```

### OpenAPIParser

The `OpenAPIParser` class is responsible for parsing OpenAPI specifications and extracting MCP tools.

```python
from openapi2mcp.openapi_parser import OpenAPIParser

# Parse an OpenAPI specification
parser = OpenAPIParser(spec_dict)

# Extract MCP tools
tools = parser.extract_tools()
```

### OAuthHandler

The `OAuthHandler` class handles OAuth authentication for API calls.

```python
from openapi2mcp.auth import OAuthHandler

# Create an OAuth handler
auth_handler = OAuthHandler({
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "token_url": "https://example.com/oauth/token"
})

# Get an access token
token = await auth_handler.get_access_token()

# Add authentication to request headers
headers = await auth_handler.add_auth_to_request({})
```

### ToolExecutor

The `ToolExecutor` class is responsible for executing MCP tools against the corresponding API endpoints.

```python
from openapi2mcp.tool_executor import ToolExecutor

# Create a tool executor
executor = ToolExecutor(tools, auth_handler)

# Execute a tool
result = await executor.execute_tool("toolName", {"param1": "value1"})
```

## MCP Server Endpoints

The MCP server exposes the following endpoints:

- `GET /mcp` - Get information about the MCP server
- `GET /mcp/tools` - Get a list of available tools
- `POST /mcp/run` - Run a tool and return the result
- `GET /mcp/sse` - Server-Sent Events endpoint for streaming tool execution

### Example Requests

#### Get MCP Server Information

```http
GET /mcp HTTP/1.1
Host: localhost:8000
```

Response:

```json
{
  "name": "OpenAPI2MCP Server",
  "version": "0.1.0",
  "supports": {
    "tools": true,
    "resources": false,
    "prompts": false
  }
}
```

#### Get Available Tools

```http
GET /mcp/tools HTTP/1.1
Host: localhost:8000
```

Response:

```json
{
  "tools": [
    {
      "name": "getUsers",
      "description": "Get all users",
      "parameters": {
        "type": "object",
        "properties": {
          "limit": {
            "type": "integer",
            "description": "Maximum number of users to return"
          }
        }
      }
    },
    ...
  ]
}
```

#### Run a Tool

```http
POST /mcp/run HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "name": "getUsers",
  "parameters": {
    "limit": 10
  }
}
```

Response:

```json
{
  "result": {
    "status_code": 200,
    "data": {
      "users": [
        { "id": 1, "name": "John Doe" },
        { "id": 2, "name": "Jane Smith" }
      ]
    },
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

## Advanced Usage

### Multiple OpenAPI Specifications

You can provide multiple OpenAPI specification files to create a single MCP server with tools from all specifications:

```bash
openapi2mcp serve --spec-file api1.yaml --spec-file api2.json --port 8000
```

### Custom Server Implementation

You can extend the basic server implementation to add custom functionality:

```python
from openapi2mcp.server import MCPServer

class CustomMCPServer(MCPServer):
    def __init__(self, spec_files, auth_config=None):
        super().__init__(spec_files, auth_config)
        
        # Add custom routes
        @self.app.get("/custom")
        async def custom_endpoint():
            return {"message": "Custom endpoint"}
    
    def custom_method(self):
        # Custom functionality
        pass

# Create a custom server
server = CustomMCPServer(["openapi.yaml"])
app = server.get_app()
```

## Troubleshooting

### Authentication Issues

If you're experiencing authentication issues:

1. Check that your OAuth credentials (client ID, client secret, token URL) are correct
2. Ensure that the API provider has authorized your application
3. Check if the token has expired (tokens are automatically refreshed, but errors can occur)

### Tool Execution Issues

If tool execution is failing:

1. Check that the API endpoint is accessible
2. Verify that the parameters you're providing are valid
3. Check the API's documentation for any specific requirements

### OpenAPI Parsing Issues

If parsing of OpenAPI specifications is failing:

1. Validate your OpenAPI specification using a tool like [Swagger Editor](https://editor.swagger.io/)
2. Check for unsupported OpenAPI features or extensions
3. Try simplifying the specification to isolate the issue

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an issue on GitHub.

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/openapi2mcp.git
   cd openapi2mcp
   ```

2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Run tests:
   ```bash
   pytest
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
