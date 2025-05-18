# Getting Started with OpenAPI2MCP

This guide will help you get started with OpenAPI2MCP, a tool that converts OpenAPI specifications to MCP servers with tools.

## Prerequisites

- Python 3.8 or higher
- An OpenAPI specification file (JSON or YAML)
- Basic familiarity with APIs

## Installation

Install OpenAPI2MCP using pip:

```bash
pip install openapi2mcp
```

## Quick Start Guide

### Step 1: Prepare an OpenAPI Specification

You'll need an OpenAPI specification file for the API you want to use. You can either:

- Use an existing OpenAPI spec file (JSON or YAML)
- Create a simplified spec for your API
- Find public specs for popular APIs

For this guide, let's create a simple API specification:

```yaml
# simple_api.yaml
openapi: 3.0.0
info:
  title: Simple API
  version: 1.0.0
servers:
  - url: https://api.example.com/v1
paths:
  /hello:
    get:
      summary: Get a greeting
      operationId: getGreeting
      parameters:
        - name: name
          in: query
          schema:
            type: string
      responses:
        '200':
          description: A greeting message
```

Save this to a file named `simple_api.yaml`.

### Step 2: Explore the Tools

First, let's see what tools OpenAPI2MCP can extract from this specification:

```bash
openapi2mcp convert --spec-file simple_api.yaml --output tools.json
```

This will create a `tools.json` file containing the MCP tools. You can examine it to see how the API endpoints were converted to tools.

### Step 3: Start the MCP Server

Now, let's start an MCP server with these tools:

```bash
openapi2mcp serve --spec-file simple_api.yaml --port 8000
```

This will start an MCP server on port 8000. You should see output confirming that the server is running.

### Step 4: Test the Server

You can test the server using curl or any HTTP client:

```bash
# Get server information
curl http://localhost:8000/mcp

# Get available tools
curl http://localhost:8000/mcp/tools

# Execute a tool
curl -X POST http://localhost:8000/mcp/run \
  -H "Content-Type: application/json" \
  -d '{
    "name": "getHello",
    "parameters": {
      "name": "World"
    }
  }'
```

### Step 5: Connect to an LLM

To use your MCP server with an LLM, you'll need:

1. An LLM or client that supports MCP
2. Configure the client to connect to your MCP server URL (`http://localhost:8000/mcp`)
3. The LLM should discover the available tools and be able to use them in its responses

## Authentication (Optional)

If your API requires authentication, you can set up OAuth credentials:

1. Create a `.env` file with the following variables:
   ```
   API_CLIENT_ID=your_client_id
   API_CLIENT_SECRET=your_client_secret
   API_TOKEN_URL=https://api.example.com/oauth/token
   ```

2. When you start the MCP server, it will use these credentials to authenticate with the API.

## Next Steps

Now that you have a basic MCP server running, you can:

1. **Integrate with more complex APIs**: Use more comprehensive OpenAPI specs
2. **Customize authentication**: Implement custom authentication logic for specific APIs
3. **Connect multiple clients**: Allow multiple LLMs or clients to use your MCP server
4. **Create client applications**: Develop applications that use your MCP server to interact with the API

Check out the [full documentation](./usage.md) and [examples](../examples/) for more information.
