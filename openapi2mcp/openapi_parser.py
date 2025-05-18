"""
Parser for converting OpenAPI specifications to MCP tools.
"""
import logging
import re
from typing import Any, Dict, List, Optional
import json
import yaml

# Import directly from openapi_parser as shown in the documentation
from openapi_parser import parse

logger = logging.getLogger(__name__)

class OpenAPIParser:
    """Parser for converting OpenAPI specifications to MCP tools."""    
    def __init__(self, spec: Dict[str, Any] | str):
        """
        Initialize the OpenAPI parser.
        
        Args:
            spec: The OpenAPI specification as a dictionary, file path, or YAML string
        """
        self.spec = spec
        
        # Convert dict to YAML string if needed
        if isinstance(spec, dict):
            yaml_str = yaml.dump(spec)
            self.specification = parse(yaml_str)
        else:
            # Assume it's already a file path or YAML string
            self.specification = parse(spec)
            
        # Set base_url from the first server if available
        self.base_url = ""
        if hasattr(self.specification, 'servers') and self.specification.servers:
            self.base_url = self.specification.servers[0].url
        
    def _generate_tool_name(self, path: str, method: str) -> str:
        """
        Generate a tool name from the path and method.
        
        Args:
            path: API endpoint path
            method: HTTP method (get, post, etc.)
            
        Returns:
            A camelCase tool name
        """
        # Remove path parameters notation
        clean_path = re.sub(r'{([^}]+)}', r'\1', path)
        
        # Convert to camelCase
        parts = [method] + [p for p in clean_path.split('/') if p]
        tool_name = parts[0].lower()
        
        for part in parts[1:]:
            if part:
                tool_name += part[0].upper() + part[1:].lower()
                
        return tool_name
    
    def _convert_schema_to_parameters(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert an OpenAPI schema to MCP tool parameters format.
        
        Args:
            schema: OpenAPI schema object
            
        Returns:
            MCP tool parameters schema
        """
        if "type" not in schema:
            return {"type": "object", "properties": {}, "required": []}
        
        result = {"type": schema["type"]}
        
        if schema["type"] == "object" and "properties" in schema:
            result["properties"] = {}
            result["required"] = []
            
            for prop_name, prop_schema in schema["properties"].items():
                result["properties"][prop_name] = {
                    "type": prop_schema.get("type", "string"),
                    "description": prop_schema.get("description", f"The {prop_name} parameter")
                }
                
                if "enum" in prop_schema:
                    result["properties"][prop_name]["enum"] = prop_schema["enum"]
                    
                if prop_schema.get("required", False):
                    result["required"].append(prop_name)
                    
        elif schema["type"] == "array" and "items" in schema:
            result["items"] = self._convert_schema_to_parameters(schema["items"])
            
        return result
    
    def _extract_parameters(self, operation: Dict[str, Any], path_params: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract parameters from an operation.
        
        Args:
            operation: OpenAPI operation object
            path_params: Path parameters from the path item
            
        Returns:
            MCP tool parameters schema
        """
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Process path parameters
        all_params = path_params.copy()
        
        # Add operation parameters
        if "parameters" in operation:
            all_params.extend(operation["parameters"])
            
        # Process all parameters
        for param in all_params:
            param_name = param["name"]
            param_schema = param.get("schema", {"type": "string"})
            
            parameters["properties"][param_name] = {
                "type": param_schema.get("type", "string"),
                "description": param.get("description", f"The {param_name} parameter")
            }
            
            if "enum" in param_schema:
                parameters["properties"][param_name]["enum"] = param_schema["enum"]
                
            if param.get("required", False):
                parameters["required"].append(param_name)
                
        # Process request body if present
        if "requestBody" in operation:
            content = operation["requestBody"].get("content", {})
            content_type = next(iter(content.keys()), None)
            
            if content_type and "schema" in content[content_type]:
                body_schema = content[content_type]["schema"]
                
                if body_schema.get("type") == "object" and "properties" in body_schema:
                    for prop_name, prop_schema in body_schema["properties"].items():
                        parameters["properties"][prop_name] = {
                            "type": prop_schema.get("type", "string"),
                            "description": prop_schema.get("description", f"The {prop_name} parameter")
                        }
                        
                        if "enum" in prop_schema:
                            parameters["properties"][prop_name]["enum"] = prop_schema["enum"]
                            
                    # Add required properties
                    if "required" in body_schema:                        
                        parameters["required"].extend(body_schema["required"])
                        
        return parameters    
    
    def extract_tools(self) -> List[Dict[str, Any]]:
        """
        Extract MCP tools from the OpenAPI specification.
        
        Returns:
            List of MCP tools
        """
        tools = []
        
        # Access paths from the parsed specification
        for path_name, path_obj in self.specification.paths.items():
            # Get path parameters if any
            path_params = []
            if hasattr(path_obj, 'parameters'):
                path_params = path_obj.parameters
                
            # Process each HTTP method
            for method_name in ['get', 'post', 'put', 'delete', 'patch']:
                method_obj = getattr(path_obj, method_name, None)
                if method_obj is None:
                    continue
                    
                # Generate tool name
                tool_name = self._generate_tool_name(path_name, method_name)
                
                # Get operation description
                description = getattr(method_obj, 'summary', '')
                if hasattr(method_obj, 'description') and method_obj.description:
                    description += f"\n\n{method_obj.description}"
                    
                # Convert the operation to a dict for parameter extraction
                operation_dict = {}
                if hasattr(method_obj, 'parameters') and method_obj.parameters:
                    operation_dict['parameters'] = [param.raw for param in method_obj.parameters]
                    
                if hasattr(method_obj, 'requestBody') and method_obj.requestBody:
                    operation_dict['requestBody'] = method_obj.requestBody.raw
                
                # Extract parameters
                parameters = self._extract_parameters(operation_dict, [param.raw for param in path_params] if path_params else [])
                
                # Create the tool
                tool = {
                    "name": tool_name,
                    "description": description,
                    "parameters": parameters,
                    "openapi_metadata": {
                        "path": path_name,
                        "method": method_name,
                        "operation_id": getattr(method_obj, 'operationId', ''),
                        "base_url": self.base_url
                    }
                }
                
                tools.append(tool)
        
        return tools
