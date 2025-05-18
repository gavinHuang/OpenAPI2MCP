```
+---------------------+     +---------------------+     +---------------------+
|                     |     |                     |     |                     |
|   OpenAPI Spec      |     |   OpenAPI2MCP       |     |   MCP-Compatible    |
|   (JSON/YAML)       +---->+   Server            +---->+   LLM/Client        |
|                     |     |                     |     |                     |
+---------------------+     +---------------------+     +---------------------+
                             |        ^
                             |        |
                             v        |
+---------------------+     +---------------------+
|                     |     |                     |
|   OAuth             |     |   API Endpoint      |
|   Authentication    +---->+   (e.g. GitHub API) |
|                     |     |                     |
+---------------------+     +---------------------+
```

# OpenAPI2MCP Architecture

## Overview

OpenAPI2MCP bridges the gap between APIs defined with OpenAPI specifications and AI systems that support the Model Context Protocol (MCP). It creates an MCP server that translates API endpoints into tools that LLMs and other AI systems can use.

## Components

1. **OpenAPI Specification (Input)**: JSON or YAML files that define API endpoints, parameters, and responses.

2. **OpenAPI2MCP Server**: The core component that:
   - Parses OpenAPI specifications
   - Extracts endpoints and converts them to MCP tools
   - Creates an MCP server that exposes these tools
   - Handles authentication with the API
   - Executes tool calls by making appropriate API requests

3. **OAuth Authentication**: Handles secure authentication to the API using OAuth credentials.

4. **API Endpoint**: The actual API service (like GitHub, Twitter, etc.) that will be called when tools are used.

5. **MCP-Compatible Client**: An LLM or other AI system that supports MCP and can discover and use the tools exposed by the server.

## Workflow

1. **Setup Phase**:
   - OpenAPI specification is loaded and parsed
   - API endpoints are converted to MCP tools
   - OAuth credentials are configured for API authentication
   - MCP server is started to expose the tools

2. **Discovery Phase**:
   - MCP client connects to the MCP server
   - Client discovers available tools through the MCP protocol
   - Client learns what capabilities are available

3. **Execution Phase**:
   - Client decides to use a tool based on user request or context
   - Client sends a tool execution request to the MCP server
   - MCP server authenticates with the API if needed
   - MCP server translates the tool request to an API call
   - API responds with data
   - MCP server formats the response and returns it to the client

## Benefits

- **Standardization**: Converts any API with an OpenAPI spec to MCP format
- **Authentication**: Handles API authentication securely
- **Tool Discovery**: Enables dynamic discovery of API capabilities
- **Seamless Integration**: Allows LLMs to interact with external APIs without custom code

## Use Cases

- Connecting LLMs to enterprise APIs
- Enabling AI systems to access public web services
- Creating custom tool ecosystems for specialized domains
- Building agentic workflows that interact with multiple services
