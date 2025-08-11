import asyncio
import logging
from fastmcp.server import FastMCP
from spoon_ai.agents.omnichain_synapse_agent import OmnichainSynapseAgent
from starlette.middleware.cors import CORSMiddleware # Import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def main():
    logger.info("Initializing OmnichainSynapseAgent for MCP server...")
    agent = OmnichainSynapseAgent()
    logger.info("Agent initialized. Setting up FastMCP server...")

    # Initialize FastMCP server
    mcp_server = FastMCP(
        name="OmnichainSynapseAgent MCP Server",
        description="MCP server for OmnichainSynapseAgent's tools",
        version="0.1.0",
    )

    # Get the underlying Starlette app from FastMCP and add CORS middleware
    starlette_app = mcp_server.sse_app()
    starlette_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080"],  # Replace with your frontend's origin
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register agent's tools with the MCP server
    for tool in agent.avaliable_tools.tools:
        mcp_server.add_tool(
            tool.execute,  # Pass the execute method as the callable
            name=tool.name,
            description=tool.description
        )
        logger.info(f"Registered tool: {tool.name}")

    # Start the SSE server transport using FastMCP's run_async method
    logger.info(f"Starting MCP server on port 8765 with SSE transport...")
    await mcp_server.run_async(transport="sse", port=8765)

if __name__ == "__main__":
    asyncio.run(main())