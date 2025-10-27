from langchain_community.chat_models import ChatOllama
from mcp.types import ListToolsResult
from langchain_core.tools import StructuredTool
from pydantic import create_model
from langchain_core.prompts import PromptTemplate

SYSTEM_PROMPT = """You are an awesome assistant that helps manage tasks. Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

# Initialize the LLM
base_llm = ChatOllama(model="phi3:3.8b", temperature=0)
from app.services.task_manager_mcp import mcp_service

# Store agent globally
agent_executor = None
tools_registry = {}


def initialise_llm(tools: ListToolsResult):
    """
    Initialize the ReAct agent with MCP tools

    Args:
        tools: List of tools from MCP service

    Returns:
        AgentExecutor instance
    """
    global agent_executor, tools_registry

    if agent_executor is None:
        try:
            # Convert MCP tools to LangChain tools
            processed_tools = []
            for a_tool in tools.tools:
                tool = wrap_mcp_tool(a_tool, mcp_service)
                processed_tools.append(tool)
                tools_registry[a_tool.name] = tool

            print("PROCESSED TOOLS", processed_tools)

            # Create prompt template for ReAct agent
            prompt = PromptTemplate.from_template(SYSTEM_PROMPT)

            # Create ReAct agent
            agent = create_react_agent(base_llm, processed_tools, prompt)

            # Create AgentExecutor
            agent_executor = AgentExecutor(
                agent=agent,
                tools=processed_tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5
            )

            print(f"✅ Agent initialized with {len(processed_tools)} tools")
            print(f"✅ Tools available: {list(tools_registry.keys())}")

            return agent_executor

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error initializing agent: {type(e).__name__}: {str(e)}")
            print(f"Full traceback:\n{error_details}")
            raise
    return agent_executor



def wrap_mcp_tool(mcp_tool, client):
    """
    Convert MCP tool metadata into a LangChain StructuredTool.
    """
    try:
        name = mcp_tool.name
        description = getattr(mcp_tool, "description", "")
        schema = mcp_tool.inputSchema

        # Dynamically build a Pydantic model for validation
        fields = {
            key: (str, ...)
            for key in schema.get("properties", {}).keys()
        }
        Model = create_model(f"{name}_Input", **fields)

        async def _run(**kwargs):
            response = await client.call_tool(name, kwargs)
            return response.get("output", response)

        return StructuredTool.from_function(
            coroutine=_run,
            name=name,
            description=description,
            args_schema=Model,
        )
    except Exception as e:
        import traceback
        print(f"Error wrapping tool {getattr(mcp_tool, 'name', 'unknown')}: {type(e).__name__}: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        raise
