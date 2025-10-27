import asyncio
import logging
from typing import Dict, List, Any, Optional

from mcp import ClientSession
from mcp.client.sse import sse_client
from app.config import settings
from mcp.types import ListToolsResult


# ─────────────────────────────
# Custom Exceptions
# ─────────────────────────────
class MCPConnectionError(Exception):
    """Raised when connection to MCP fails."""


class MCPTimeoutError(Exception):
    """Raised when MCP request times out."""


# ─────────────────────────────
# MCP Client
# ─────────────────────────────
class TaskManagerMCP:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.read_stream = None
        self.write_stream = None
        self.client_context = None
        self.session_context = None
        self.is_connected = False

        # Retry settings
        self.retry_attempts = getattr(settings, "MCP_RETRY_ATTEMPTS", 3)
        self.retry_delay = getattr(settings, "MCP_RETRY_DELAY", 2)

        # Auto-detect URL from env or default
        # Default to your Comment MCP on port 8001
        self.url = getattr(settings, "MCP_URL", "http://127.0.0.1:8001/sse")

        # Optional timeout for connect and calls
        self.connect_timeout = getattr(settings, "MCP_CONNECT_TIMEOUT", 5)
        self.call_timeout = getattr(settings, "MCP_CALL_TIMEOUT", 10)

        # Logging setup
        self.logger = logging.getLogger("TaskManagerMCP")
        logging.basicConfig(level=logging.INFO)

    # ─────────────────────────────
    async def connect(self) -> bool:
        """Connect to MCP server with automatic retry logic."""
        for attempt in range(1, self.retry_attempts + 1):
            try:
                await self._cleanup_existing_connections()
                self.logger.info(f"Connecting to MCP server: {self.url} (Attempt {attempt})")

                # Create SSE client and session
                self.client_context = sse_client(self.url)
                self.read_stream, self.write_stream = await self.client_context.__aenter__()

                self.session_context = ClientSession(self.read_stream, self.write_stream)
                self.session = await self.session_context.__aenter__()
                await self.session.initialize()

                self.is_connected = True
                self.logger.info(f"✅ Connected to MCP at {self.url}")
                return True

            except Exception as e:
                self.logger.warning(f"⚠️ Connection attempt {attempt} failed: {e}")
                if attempt < self.retry_attempts:
                    self.logger.info(f"Retrying in {self.retry_delay}s...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logger.error(f"❌ Failed to connect to MCP after {attempt} attempts")
                    return False

    # ─────────────────────────────
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server with automatic reconnection."""
        if not self.is_connected:
            await self.connect()
            if not self.is_connected:
                raise MCPConnectionError("Unable to connect to MCP service")

        try:
            self.logger.info(f"🧰 Calling tool '{tool_name}' with args: {arguments}")
            result = await asyncio.wait_for(
                self.session.call_tool(tool_name, arguments=arguments),
                timeout=self.call_timeout,
            )
            self.logger.info(f"✅ Tool '{tool_name}' executed successfully")
            return result
        except asyncio.TimeoutError:
            raise MCPTimeoutError(f"Timeout calling tool '{tool_name}'")
        except Exception as e:
            self.logger.error(f"Error calling MCP tool '{tool_name}': {e}")
            raise

    # ─────────────────────────────
    async def list_tools(self) -> ListToolsResult:
        """List available tools from MCP."""
        if not self.is_connected:
            await self.connect()
        return await self.session.list_tools()

    # ─────────────────────────────
    async def close(self):
        """Gracefully close MCP connection."""
        try:
            if self.session_context:
                await self.session_context.__aexit__(None, None, None)
            if self.client_context:
                await self.client_context.__aexit__(None, None, None)
            self.is_connected = False
            self.logger.info("🔌 MCP connection closed.")
        except Exception as e:
            self.logger.error(f"Error closing MCP connection: {e}")

    # ─────────────────────────────
    async def _cleanup_existing_connections(self):
        """Clean up previous open connections."""
        if self.is_connected:
            try:
                await self.close()
            except Exception as e:
                self.logger.warning(f"Cleanup failed: {e}")


# ─────────────────────────────
# Singleton instance
# ─────────────────────────────
mcp_service = TaskManagerMCP()
