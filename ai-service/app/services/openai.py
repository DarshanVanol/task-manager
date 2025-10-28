import json
import httpx
from typing import Any, Dict, List, Optional
from mcp.types import ListToolsResult
from app.services.task_manager_mcp import mcp_service

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:1b"

SYSTEM_PROMPT = """You are an awesome task management assistant that helps users manage their tasks.
- Use the available tools to fetch, create, update, or delete tasks as needed.
- Always provide clear and helpful responses to the user.
- When you need information, use the appropriate tool before responding."""

# Store tools globally
tools_spec = []
tool_implementations = {}


def format_mcp_tools_for_ollama(tools: ListToolsResult) -> List[Dict[str, Any]]:
    """Convert MCP tools to Ollama function calling format"""
    global tools_spec, tool_implementations

    tools_spec = []
    tool_implementations = {}

    for tool in tools.tools:
        tool_name = tool.name
        description = getattr(tool, "description", "No description")
        schema = tool.inputSchema if hasattr(tool, "inputSchema") else {}

        # Format for Ollama
        tool_spec = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": (
                    schema if schema else {"type": "object", "properties": {}}
                ),
            },
        }

        tools_spec.append(tool_spec)
        tool_implementations[tool_name] = tool

    return tools_spec


async def call_ollama(
    messages: List[Dict[str, str]], tools: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Make a call to Ollama API with tools support"""
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }

    # Only include tools if they exist
    if tools:
        payload["tools"] = tools

    print(f"PAYLOAD {payload}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(OLLAMA_URL, json=payload)

        # Check for errors
        if response.status_code != 200:
            error_text = response.text
            print(f"❌ Ollama API error ({response.status_code}): {error_text}")

            # If tools are not supported, try without tools
            if "tools" in payload and response.status_code == 400:
                print("⚠️ Tools not supported, retrying without tools...")
                payload.pop("tools", None)
                response = await client.post(OLLAMA_URL, json=payload)

        response.raise_for_status()
        return response.json()


async def execute_tool(tool_name: str, arguments: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
    """Execute an MCP tool and return the result"""
    try:
        # Inject the token into the arguments if provided
        arguments_with_token = {**arguments}
        if token:
            arguments_with_token["token"] = token
        
        result = await mcp_service.call_tool(tool_name, arguments_with_token)

        # Extract content from CallToolResult
        if hasattr(result, "content"):
            content = result.content
            if isinstance(content, list) and len(content) > 0:
                # Get the first content item (usually TextContent)
                first_content = content[0]
                if hasattr(first_content, "text"):
                    text = first_content.text
                    # Try to parse as JSON if possible
                    try:
                        parsed = json.loads(text)
                        return {"success": True, "result": parsed}
                    except json.JSONDecodeError:
                        return {"success": True, "result": text}
                else:
                    return {"success": True, "result": str(first_content)}
            else:
                return {"success": True, "result": str(content)}
        else:
            return {"success": True, "result": str(result)}
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def run_agent(
    user_prompt: str,
    token: str,
    tools: Optional[ListToolsResult] = None,
) -> str:
    """
    Run the agent with tool calling loop

    Args:
        user_prompt: The user's input message
        tools: Optional MCP tools to use

    Returns:
        The final response from the agent
    """
    # Format tools if provided
    if tools:
        format_mcp_tools_for_ollama(tools)

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    # Safety: limit tool-call iterations to prevent infinite loops
    max_iterations = 8

    for iteration in range(max_iterations):
        print(f"🔄 Agent iteration {iteration + 1}/{max_iterations}")

        # Call Ollama
        response = await call_ollama(messages, tools_spec)

        # Extract the assistant message
        assistant_msg = response.get("message")
        if not assistant_msg:
            return "[Agent error: no message in response]"

        content = assistant_msg.get("content", "")
        tool_calls = assistant_msg.get("tool_calls", [])

        # If no tool calls, we have the final answer
        if not tool_calls:
            print(f"✅ Final answer: {content}")
            messages.append({"role": "assistant", "content": content})
            return content

        # Add assistant message with tool calls
        messages.append(
            {"role": "assistant", "content": content, "tool_calls": tool_calls}
        )

        # Execute each tool call
        for tool_call in tool_calls:
            function_info = tool_call.get("function", {})
            fn_name = function_info.get("name")
            raw_args = function_info.get("arguments", {})

            # Parse arguments if they're a string
            if isinstance(raw_args, str):
                try:
                    raw_args = json.loads(raw_args)
                except json.JSONDecodeError:
                    raw_args = {}

            print(f"🔧 Calling tool: {fn_name} with args: {raw_args}")

            # Execute the tool with the user's token
            if fn_name in tool_implementations:
                tool_result = await execute_tool(fn_name, raw_args, token)
            else:
                tool_result = {"error": f"Unknown tool: {fn_name}"}

            print(f"📥 Tool result: {tool_result}")

            # Add tool result to messages
            messages.append(
                {"role": "tool", "name": fn_name, "content": json.dumps(tool_result)}
            )

    return "[Agent error: Maximum iterations reached without final answer]"


def initialise_llm(tools: ListToolsResult):
    """
    Initialize by formatting the tools (no agent object needed)

    Args:
        tools: List of MCP tools

    Returns:
        True if successful
    """
    try:
        format_mcp_tools_for_ollama(tools)
        print(f"✅ Tools formatted: {len(tools_spec)} tools available")
        print(f"✅ Tools: {[t['function']['name'] for t in tools_spec]}")
        return True
    except Exception as e:
        import traceback

        print(f"Error formatting tools: {type(e).__name__}: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        raise
