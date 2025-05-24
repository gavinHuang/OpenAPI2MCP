"""
Tool executor for running MCP tools against the OpenAPI endpoints.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union # Added Union for completeness if needed by generated hints

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

    def _openapi_type_to_python_hint(self, schema: Dict[str, Any]) -> str:
        """Converts an OpenAPI schema type to a Python type hint string."""
        openapi_type = schema.get("type")
        hint = "Any"  # Default if type is unknown or not specified
        if openapi_type == "string":
            # TODO: Consider schema.get("format") for more specific types like date, datetime, byte, binary
            hint = "str"
        elif openapi_type == "integer":
            hint = "int"
        elif openapi_type == "number":
            hint = "float" # OpenAPI 'number' typically maps to float
        elif openapi_type == "boolean":
            hint = "bool"
        elif openapi_type == "array":
            items_schema = schema.get("items", {})
            if not items_schema:  # array of anything if items is not specified
                item_hint = "Any"
            else:
                item_hint = self._openapi_type_to_python_hint(items_schema)  # Recursive call for item type
            hint = f"List[{item_hint}]"
        elif openapi_type == "object":
            # For simplicity, mapping to Dict[str, Any].
            # A more complex implementation could try to generate a TypedDict or similar
            # based on schema.get("properties").
            hint = "Dict[str, Any]"
        return hint

    def _get_default_value_repr(self, param_spec: Dict[str, Any], is_required: bool) -> Optional[str]:
        """
        Determines the string representation of a parameter's default value for a Python function signature.
        Returns None if there's no default value to be explicitly stated in the signature (e.g. required param with no default).
        """
        if "default" in param_spec:
            default_val = param_spec["default"]
            if isinstance(default_val, str):
                return f"'{default_val}'"  # Ensure strings are quoted
            elif isinstance(default_val, bool):
                return "True" if default_val else "False"
            # For numbers (int, float) and None itself, their standard repr() is usually fine.
            return repr(default_val)
        else:  # No explicit 'default' keyword in the spec
            if not is_required:
                # If the parameter is optional (not required) and has no explicit default,
                # its Python signature default should be None.
                return "None"
            # If required and no 'default' keyword, it has no default in the Python signature.
            return None

    def get_tool_function_for_registration(self, tool_name: str) -> Callable[..., Awaitable[str]]:
        """
        Creates an awaitable callable function for a specific tool that can be
        registered with FastMCP's add_tool method.

        This function is dynamically generated with a specific signature matching
        the tool's parameters as defined in the OpenAPI specification.

        Args:
            tool_name: The name of the tool.

        Returns:
            An awaitable callable with an explicit signature. It accepts tool 
            parameters as defined in the spec and returns a JSON string 
            representing the execution result.
        
        Raises:
            ValueError: If the tool_name is not found in self.tools or if
                        parameter definitions are missing/malformed.
        """
        if tool_name not in self.tools:
            logger.error(f"Attempted to get a tool function for non-existent tool: {tool_name}")
            raise ValueError(f"Tool '{tool_name}' not found, cannot create registration function.")

        tool_spec = self.tools[tool_name]
        
        parameters_input = tool_spec.get("parameters")

        processed_parameter_details: List[Dict[str, Any]] = []

        if isinstance(parameters_input, list):
            raw_openapi_params_list = parameters_input
            if not raw_openapi_params_list:
                logger.info(f"Tool '{tool_name}' has an empty 'parameters' list. Assuming no parameters.")
            else:
                logger.info(f"Tool '{tool_name}' has 'parameters' as a list. Processing items as individual parameters.")
                for param_spec in raw_openapi_params_list:
                    name = param_spec.get("name")
                    if not name:
                        logger.warning(f"Skipping parameter with no name in list for tool '{tool_name}': {param_spec}")
                        continue

                    is_required = param_spec.get("required", False)
                    if param_spec.get("in") == "path": # Path parameters are always required
                        is_required = True

                    schema = param_spec.get("schema", {})
                    if not schema and param_spec.get("content"): 
                        content_schema = next(iter(param_spec.get("content", {}).values()), {}).get("schema",{})
                        schema = content_schema if content_schema else {}
                    
                    python_type_hint_str = self._openapi_type_to_python_hint(schema)
                    # For list items, param_spec itself might contain 'default'
                    default_value_str_repr = self._get_default_value_repr(param_spec, is_required)
                    
                    processed_parameter_details.append({
                        "name": name,
                        "python_type_hint": python_type_hint_str,
                        "default_value_repr": default_value_str_repr,
                        "is_required": is_required
                    })

        elif isinstance(parameters_input, dict) and parameters_input.get("type") == "object" and "properties" in parameters_input:
            logger.info(f"Tool '{tool_name}' has 'parameters' as an object schema. Processing its properties.")
            object_schema = parameters_input
            object_properties = object_schema.get("properties", {})
            object_required_fields = object_schema.get("required", [])

            if not object_properties:
                logger.info(f"Tool '{tool_name}' 'parameters' object schema has no properties. Assuming no parameters from this source.")
            else:
                for prop_name, prop_schema in object_properties.items():
                    name = prop_name
                    current_param_schema = prop_schema # The schema for the property is prop_schema itself
                    
                    is_required = prop_name in object_required_fields
                    
                    python_type_hint_str = self._openapi_type_to_python_hint(current_param_schema)
                    # For object properties, prop_schema might contain 'default'
                    default_value_str_repr = self._get_default_value_repr(current_param_schema, is_required)
                    
                    processed_parameter_details.append({
                        "name": name,
                        "python_type_hint": python_type_hint_str,
                        "default_value_repr": default_value_str_repr,
                        "is_required": is_required
                    })
        
        elif parameters_input is None:
            logger.info(f"Tool '{tool_name}' does not have a 'parameters' key or it is null. Assuming no parameters.")
        else:
            logger.warning(
                f"Tool '{tool_name}' has 'parameters' in an unexpected format: {type(parameters_input)}. "
                f"Expected a list of parameters or an object schema with properties. Assuming no parameters."
            )

        # The rest of the function uses processed_parameter_details
        # param_strings, param_names_for_body are derived from processed_parameter_details

        param_strings = []
        param_names_for_body = []

        if not processed_parameter_details: # No parameters for this tool
            logger.info(f"Tool '{tool_name}' has no parameters. Generating a function with no arguments.")
        else:
            for p_def in processed_parameter_details:
                name = p_def.get("name")
                base_type_hint = p_def.get("python_type_hint", "Any")
                default_repr = p_def.get("default_value_repr") # This is "None", "'value'", "123", or actual None
                is_param_required = p_def.get("is_required", False)

                final_type_hint = base_type_hint
                # If param is not required, and its default representation is the string "None" (meaning it defaults to None)
                # then we should wrap its base type with Optional.
                if not is_param_required and default_repr == "None":
                    final_type_hint = f"Optional[{base_type_hint}]"
                
                param_str = f"{name}: {final_type_hint}"
                if default_repr is not None: # If there's any default value representation (e.g. "None", "'val'", "10")
                    param_str += f" = {default_repr}"
                # If default_repr is None (meaning required param with no default), no " = ..." is added.
                
                param_strings.append(param_str)
                param_names_for_body.append(name)

        signature_params_str = ", ".join(param_strings)
        
        # Ensure 'tool_name' is treated as a literal string in the generated function
        # by embedding it directly or passing it safely into the exec scope.
        # Using it directly in the f-string for the function body is simplest here.

        func_source_lines = []
        func_source_lines.append(f"async def generated_tool_func({signature_params_str}) -> str:")
        func_source_lines.append("    params_dict = {}")
        for p_name in param_names_for_body:
            func_source_lines.append(f"    params_dict['{p_name}'] = {p_name}")
        
        # Using an f-string to embed tool_name directly into the generated code.
        # This makes tool_name a literal within the generated function's scope.
        func_source_lines.append(f"    # Dynamically generated for tool: {tool_name}")
        func_source_lines.append(f"    execution_result = await self.execute_tool(tool_name='{tool_name}', params=params_dict)")
        func_source_lines.append("    return json.dumps(execution_result)")
        
        function_source = "\n".join(func_source_lines)
        
        logger.debug(f"Generated source for tool '{tool_name}':\n{function_source}")

        # Prepare the local namespace for exec. `self` and `json` are needed by the generated function.
        # Types like Optional, List, etc., if used in python_type_hint, must be available.
        # They are imported at the module level, so globals() should provide them.
        local_namespace = {
            'self': self,
            'json': json,
            # The following are needed if type hints like "Optional[str]" are used in the generated signature string
            'Optional': Optional, 
            'List': List, 
            'Dict': Dict, 
            'Any': Any,
            'Union': Union
        }
        
        # globals() provides builtins and module-level imports (like Optional, List)
        # local_namespace provides 'self' and 'json' for the function body.
        exec_globals = {**globals(), **local_namespace} # Make sure local_namespace types override if there's a clash
                                                        # though module level imports are preferred.
                                                        # More simply, ensure types are in globals()

        try:
            exec(function_source, exec_globals, local_namespace)
        except Exception as e:
            logger.error(f"Failed to exec generated function for tool '{tool_name}'. Source:\n{function_source}\nError: {e}")
            raise
            
        return local_namespace['generated_tool_func']
