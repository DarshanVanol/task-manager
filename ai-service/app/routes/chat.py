from fastapi import APIRouter, Body, Request, HTTPException
from pydantic import BaseModel
from app.services.openai import llm
import logging
from langchain.messages import AIMessage

router = APIRouter(prefix="/chat")


class InputMessage(BaseModel):
    text: str


class ChatResponse(BaseModel):
    output: str
    success: bool


@router.post("/", response_model=ChatResponse)
async def create_chat(request: Request, input: InputMessage = Body()):
    """
    Chat endpoint that uses the agent with MCP tools
    """
    try:

        # Get agent from app state
        llm = request.app.state.llm

        if llm is None:
            raise HTTPException(
                status_code=503,
                detail="Agent not initialized. MCP service may not be connected.",
            )

        logging.info("HI")
        # Invoke the agent with the user input
        result = llm.invoke(input.text)

        logging.info("RESULT", result)


        return ChatResponse(
            output=result, success=True
        )

    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")
