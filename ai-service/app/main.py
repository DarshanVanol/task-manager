from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.services import task_manager_mcp
from app.config import settings
from app.routes import chat
from app.services.openai import initialise_llm
from pydantic import BaseModel


class InputMessage(BaseModel):
    text: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code (runs before app starts)
    print(f"Starting application on port {settings.PORT}...")
    try:
        is_mcp_connected = await task_manager_mcp.mcp_service.connect()
        if is_mcp_connected:
            print("MCP Connected")
            try:
                tools = await task_manager_mcp.mcp_service.list_tools()
                print("Available tools:", tools)
                initialise_llm(tools=tools)
                print("✅ LLM initialized with tools")
                
                # Store tools and mcp_service in app state for use in routes
                app.state.tools = tools
                app.state.mcp_service = task_manager_mcp.mcp_service
                
            except Exception as e:
                print(f"Failed to list tools: {e}")
                app.state.tools = None
        else:
            print("Failed to connect to MCP")
            app.state.tools = None
    except Exception as e:
        print(f"Error during startup: {e}")
        app.state.tools = None
    
    print("Application startup complete")
    yield
    
    # Shutdown code (runs when app stops)
    try:
        await task_manager_mcp.mcp_service.close()
    except Exception as e:
        print(f"Error during shutdown: {e}")
    print("Application shutdown complete")


app = FastAPI(lifespan=lifespan)

app.include_router(chat.router, prefix="/api/v1")


@app.get("/")
def health_check():
    return {"status": "Ok", "port": settings.PORT}


@app.get("/config")
def config_info():
    return {
        "port": settings.PORT,
        "mcp_url": settings.MCP_URL,
        "environment": "development"
    }