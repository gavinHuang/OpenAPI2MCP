# Example: GitHub API Integration

This example demonstrates how to use OpenAPI2MCP to create an MCP server with tools based on the GitHub API.

## Prerequisites

1. A GitHub account
2. A personal access token with appropriate permissions
3. OpenAPI2MCP installed (`pip install openapi2mcp`)

## Step 1: Get GitHub API OpenAPI Specification

First, we need to get the OpenAPI specification for the GitHub API. You can find it in various places, but for this example, we'll use a simplified version focused on repository operations.

Create a file named `github_api.yaml` with the following content:

```yaml
openapi: 3.0.0
info:
  title: GitHub API
  description: A simplified GitHub API specification for demonstration purposes
  version: 1.0.0
servers:
  - url: https://api.github.com
paths:
  /repos/{owner}/{repo}:
    get:
      summary: Get repository information
      description: Get details about a specific repository
      operationId: getRepository
      parameters:
        - name: owner
          in: path
          description: The account owner of the repository
          required: true
          schema:
            type: string
        - name: repo
          in: path
          description: The name of the repository
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Repository information
  /repos/{owner}/{repo}/issues:
    get:
      summary: List repository issues
      description: Get a list of issues for a repository
      operationId: listRepositoryIssues
      parameters:
        - name: owner
          in: path
          description: The account owner of the repository
          required: true
          schema:
            type: string
        - name: repo
          in: path
          description: The name of the repository
          required: true
          schema:
            type: string
        - name: state
          in: query
          description: Indicates the state of the issues to return
          schema:
            type: string
            enum: [open, closed, all]
            default: open
        - name: per_page
          in: query
          description: Results per page (max 100)
          schema:
            type: integer
            default: 30
        - name: page
          in: query
          description: Page number of the results to fetch
          schema:
            type: integer
            default: 1
      responses:
        '200':
          description: List of issues
    post:
      summary: Create an issue
      description: Create a new issue in a repository
      operationId: createIssue
      parameters:
        - name: owner
          in: path
          description: The account owner of the repository
          required: true
          schema:
            type: string
        - name: repo
          in: path
          description: The name of the repository
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - title
              properties:
                title:
                  type: string
                  description: The title of the issue
                body:
                  type: string
                  description: The body of the issue
                labels:
                  type: array
                  items:
                    type: string
                  description: Labels to associate with this issue
                assignees:
                  type: array
                  items:
                    type: string
                  description: Logins for Users to assign to this issue
      responses:
        '201':
          description: Issue created
```

## Step 2: Set Up Authentication

Create a `.env` file with your GitHub personal access token:

```
API_CLIENT_ID=your_github_username
API_CLIENT_SECRET=your_personal_access_token
API_TOKEN_URL=https://github.com/login/oauth/access_token
```

Or, if you prefer to use token authentication directly, create a Python script that sets up the authentication:

```python
import os
import uvicorn
from openapi2mcp.server import MCPServer
from openapi2mcp.auth import OAuthHandler

# Custom authentication handler for GitHub token
class GitHubTokenHandler(OAuthHandler):
    def __init__(self, token):
        self.token = token
    
    async def get_access_token(self):
        return self.token
    
    async def add_auth_to_request(self, headers):
        headers["Authorization"] = f"token {self.token}"
        return headers

# Get token from environment
github_token = os.environ.get("GITHUB_TOKEN")
if not github_token:
    raise ValueError("GITHUB_TOKEN environment variable is not set")

# Create authentication handler
auth_handler = GitHubTokenHandler(github_token)

# Create MCP server
server = MCPServer(
    spec_files=["github_api.yaml"],
    auth_config=None  # We'll manually set the auth_handler
)

# Set the auth handler
server.auth_handler = auth_handler
server.tool_executor.auth_handler = auth_handler

# Run the server
app = server.get_app()
uvicorn.run(app, host="127.0.0.1", port=8000)
```

Save this as `github_mcp_server.py`.

## Step 3: Start the MCP Server

### Using the CLI (with environment variables)

```bash
export GITHUB_TOKEN=your_personal_access_token
openapi2mcp serve --spec-file github_api.yaml --port 8000
```

### Using the Python Script

```bash
export GITHUB_TOKEN=your_personal_access_token
python github_mcp_server.py
```

## Step 4: Use the MCP Server with an LLM

Now you can connect to your MCP server from any MCP-compatible client. Here's an example using a simple Python script:

```python
import requests
import json

# MCP server URL
mcp_url = "http://127.0.0.1:8000/mcp"

# Get available tools
response = requests.get(f"{mcp_url}/tools")
tools = response.json()["tools"]

print(f"Available tools:")
for tool in tools:
    print(f"- {tool['name']}: {tool.get('description', '')}")

# Use the getRepository tool
print("\nGetting repository information...")
response = requests.post(
    f"{mcp_url}/run",
    json={
        "name": "getReposOwnerRepo",
        "parameters": {
            "owner": "openai",
            "repo": "openai-python"
        }
    }
)

result = response.json()["result"]
print(f"Status code: {result['status_code']}")
print(json.dumps(result["data"], indent=2))

# Use the listRepositoryIssues tool
print("\nListing repository issues...")
response = requests.post(
    f"{mcp_url}/run",
    json={
        "name": "getReposOwnerRepoIssues",
        "parameters": {
            "owner": "openai",
            "repo": "openai-python",
            "state": "open",
            "per_page": 5
        }
    }
)

result = response.json()["result"]
print(f"Status code: {result['status_code']}")
issues = result["data"]
for issue in issues[:5]:  # First 5 issues
    print(f"#{issue['number']} - {issue['title']}")
```

Save this as `github_mcp_client.py` and run it:

```bash
python github_mcp_client.py
```

## Example Output

```
Available tools:
- getReposOwnerRepo: Get repository information
- getReposOwnerRepoIssues: List repository issues
- postReposOwnerRepoIssues: Create an issue

Getting repository information...
Status code: 200
{
  "id": 1234567,
  "name": "openai-python",
  "full_name": "openai/openai-python",
  "private": false,
  "owner": {
    "login": "openai",
    "id": 14957082,
    ...
  },
  ...
}

Listing repository issues...
Status code: 200
#1234 - Cannot install package in Python 3.8
#1233 - Add support for new models
#1232 - Documentation improvements for streaming
#1231 - Error handling in async mode
#1230 - Feature request: better error messages
```

## Integrating with LLMs

To use this MCP server with an LLM that supports MCP, you would point the LLM to your MCP server URL (`http://127.0.0.1:8000/mcp`).

When the LLM wants to interact with the GitHub API, it will automatically discover and use the appropriate tools from your MCP server, allowing it to perform operations like:

1. Getting repository information
2. Listing repository issues
3. Creating new issues

This enables the LLM to interact with GitHub in a controlled manner through the standardized MCP interface.

## Extending the Example

You can extend this example by:

1. Adding more GitHub API endpoints to the OpenAPI specification
2. Creating a more comprehensive authentication handler
3. Adding custom tooling on top of the GitHub API
4. Integrating with other APIs alongside GitHub

The OpenAPI2MCP tool makes it easy to create MCP servers for any API that has an OpenAPI specification, enabling seamless integration with LLMs that support the Model Context Protocol.
