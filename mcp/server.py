# server.py
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from comment_client import CommentClient

mcp = FastMCP(
    "Comment MCP",
    host="127.0.0.1",
    port=8001,
)


@mcp.tool(name="fetch_comments", description="Fetch comments for given entity")
async def get_comments(
    entity_id: int = Field(description="Entity id of comments to fetch"),
    token: str = Field(description="Access token of user"),
):
    try:
        cc = CommentClient(token=token)
        return cc.fetch_comments(entity_id=entity_id)
    except Exception as e:
        return {"error": str(e), "entity_id": entity_id}


@mcp.tool(name="create_comment", description="Create comment for given entity")
async def get_comments(
    entity_id: int = Field(description="Entity id of comments to create"),
    token: str = Field(description="Access token of user"),
    content: str = Field(description="Text content of comment"),
):
    try:
        cc = CommentClient(token=token)
        return cc.create_comment(entity_id=entity_id, content=content)
    except Exception as e:
        return {"error": str(e), "entity_id": entity_id}


if __name__ == "__main__":
    mcp.run(transport="sse")
