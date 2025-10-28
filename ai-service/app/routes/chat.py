from fastapi import APIRouter, Body, Request, HTTPException, Depends
from pydantic import BaseModel
import logging
from app.services.openai import run_agent
from app.dependencies import User, get_current_user

router = APIRouter(prefix="/chat")


class InputMessage(BaseModel):
    text: str


class ChatResponse(BaseModel):
    output: str
    success: bool


@router.post("/")
async def create_chat(request: Request, input: InputMessage = Body(),user:User = Depends(get_current_user) ):
    """
    Chat endpoint that uses the agent with MCP tools
    """
    try:
        # Get tools from app state
        tools = request.app.state.tools

        if tools is None:
            raise HTTPException(
                status_code=503,
                detail="Tools not initialized. MCP service may not be connected.",
            )

        logging.info(f"🚀 Processing chat request: {input.text}")
        
        # Run the agent with tool calling loop
        result = await run_agent(input.text, user.token, tools)

        logging.info(f"✅ Agent response: {result}")

        return result

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Chat error: {type(e).__name__}: {str(e)}")
        logging.error(f"Full traceback:\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")
