"""
Parser for converting OpenAPI specifications to MCP tools.
"""
import logging
import re
from typing import Any, Dict, List, Optional
import json
import yaml
import prance # Added import for prance

logger = logging.getLogger(__name__)

class OpenAPIParser:
    """Parser for converting OpenAPI specifications to MCP tools."""    
    def __init__(self, spec: Dict[str, Any] | str):
        """
        Initialize the OpenAPI parser.
        
        Args:
            spec: The OpenAPI specification as a dictionary, file path, or YAML string
        """
        self.spec_input = spec # Store the original input for prance

        if isinstance(spec, dict):
            # Prance expects a file path or URL, so if it's a dict,
            # we might need to save it to a temporary file or adjust usage.
            # For now, let's assume if it's a dict, it's already resolved
            # or prance needs to be handled differently for dict inputs.
            # This part might need refinement based on how dict inputs are handled.
            # Directly using a dict with ResolvingParser might not work as it expects a path.
            # A common pattern is to dump it to a temporary YAML/JSON file.
            # However, to keep it simple and aligned with prance's primary use case (file paths):
            # We'll raise an error or handle dicts by converting them if prance requires a file path.
            # For this example, we'll assume 'spec' will be a file path or URL string for prance.
            # If spec is a dict, the original code attempted to parse it directly.
            # Prance's ResolvingParser typically takes a URL or file path.
            # To handle a dict, one might need to dump it to a string or temp file.
            # For now, this example will focus on file path/URL usage with prance.
            # If a dict is passed, the behavior of prance.ResolvingParser(spec_str) would depend on prance's internals.
            # Let's adjust to what prance.ResolvingParser expects, which is typically a path.
            # If spec is a dict, we'll convert it to a YAML string, and prance might handle it.
            # Alternatively, prance might need a file path.
            # The example `parser = prance.ResolvingParser('your_spec.yaml')` implies file path.
            # Let's assume if 'spec' is not a string (path/URL), it's a pre-loaded dict.
            # Prance's constructor can take `spec_string` argument.
            parser = prance.ResolvingParser(spec_string=yaml.dump(spec), strict=False)
        elif isinstance(spec, str):
            # Assume 'spec' is a file path or URL
            parser = prance.ResolvingParser(spec, strict=False)
        else:
            raise TypeError("Spec must be a dictionary, file path, or URL string.")

        self.specification_dict = parser.specification # prance gives a dict

        # Adapt access to servers and paths for a dictionary structure
        self.base_url = ""
        if 'servers' in self.specification_dict and self.specification_dict['servers']:
            self.base_url = self.specification_dict['servers'][0].get('url', "")
        
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
        
        # Access paths from the parsed specification (now a dict)
        for path_name, path_obj_dict in self.specification_dict.get('paths', {}).items():
            # Get path parameters if any
            path_params_list = path_obj_dict.get('parameters', [])
                
            # Process each HTTP method
            for method_name in ['get', 'post', 'put', 'delete', 'patch']:
                method_obj_dict = path_obj_dict.get(method_name)
                if method_obj_dict is None:
                    continue
                    
                # Generate tool name
                tool_name = self._generate_tool_name(path_name, method_name)
                
                # Get operation description
                description = method_obj_dict.get('summary', '')
                if method_obj_dict.get('description'):
                    description += f"\\n\\n{method_obj_dict['description']}"
                    
                # Extract parameters
                # The method_obj_dict is already a dictionary.
                # path_params_list is also a list of dictionaries.
                parameters = self._extract_parameters(method_obj_dict, path_params_list)
                
                # Create the tool
                tool = {
                    "name": tool_name,
                    "description": description,
                    "parameters": parameters,
                    "openapi_metadata": {
                        "path": path_name,
                        "method": method_name,
                        "operation_id": method_obj_dict.get('operationId', ''),
                        "base_url": self.base_url
                    }
                }
                
                tools.append(tool)
        
        return tools
