# OpenAPI2MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://www.python.org/)

OpenAPI2MCP is a Python tool that serves as a Model Context Protocol (MCP) server with tools generated from OpenAPI specification files (JSON or YAML). It allows LLMs and AI applications that support MCP to interact with any API that has an OpenAPI specification.

## Features

- 🔄 Convert OpenAPI specifications to MCP tools
- 🛠️ Serve MCP endpoints with tools from OpenAPI specs
- 🔐 OAuth authentication support for API calls
- 📡 Server-Sent Events (SSE) support for real-time communication
- 💻 Command-line interface for easy usage
- 🧩 Programmatic API for integration into other applications

## Installation

```bash
pip install openapi2mcp
```

## Quick Start

### Convert an OpenAPI spec to MCP tools:

```bash
openapi2mcp convert --spec-file openapi.yaml --output tools.json
```

### Start an MCP server with tools from an OpenAPI spec:

```bash
openapi2mcp serve --spec-file openapi.yaml --port 8000
```

### Use environment variables for OAuth authentication:

```
API_CLIENT_ID=your_client_id
API_CLIENT_SECRET=your_client_secret
API_TOKEN_URL=https://example.com/oauth/token
```

## Documentation

- [Getting Started](docs/getting_started.md)
- [Usage Documentation](docs/usage.md)
- [Architecture](docs/architecture.md)
- [GitHub API Example](docs/github_example.md)

## Examples

The [examples](examples/) directory contains sample code to help you get started:

- [Sample API specification](examples/sample_api.yaml)
- [Basic server example](examples/run_server.py)
- [Client example](examples/client_example.py)
- [Advanced usage](examples/advanced_usage.py)

## How It Works

OpenAPI2MCP bridges the gap between APIs defined with OpenAPI specifications and AI systems that support the Model Context Protocol (MCP):

1. It parses OpenAPI specifications to extract API endpoints
2. Converts these endpoints into MCP tools with appropriate parameters
3. Creates an MCP server that exposes these tools
4. Handles authentication with the API
5. Executes tool calls by making appropriate API requests

This allows AI models and applications to interact with any API through the standardized MCP interface.

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

## Why Use OpenAPI2MCP?

- **Universal API Access**: Connect any OpenAPI-defined API to MCP-compatible LLMs
- **Tool Discovery**: LLMs can dynamically discover what capabilities are available
- **Authentication Handling**: Securely manage API credentials
- **Standard Interface**: Consistent way to interact with diverse APIs
- **Easy Integration**: Simple setup process for both local and production use

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Install development dependencies (`pip install -e ".[dev]"`)
4. Make your changes
5. Run tests (`pytest`)
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
