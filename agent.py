import os
from typing import Any, Optional

from mcp.client.stdio import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient


class MongoDBSearchAgent:
    """Strands agent using Local MongoDB MCP tools via Stdio."""

    def __init__(
        self,
        name: str = "mongodb-search-agent",
        description: str = "Searches MongoDB Atlas using natural-language queries.",
    ):
        self.name = name
        self.description = description

        # Configure the local MCP server process parameters
        connection_string = os.getenv("MONGODB_URI")
        if not connection_string:
            raise ValueError("Environment variable MONGODB_URI is not set.")

        mcp_command = os.getenv(
            "MCP_COMMAND",
            "npx.cmd" if os.name == "nt" else "npx",
        )

        self.server_params = StdioServerParameters(
            command=mcp_command,
            args=[
                "mongodb-mcp-server",
                "--transport",
                "stdio",
                "--connectionString",
                connection_string,
                "--readOnly",
            ],
        )

        self.mongo_client = MCPClient(
            lambda: stdio_client(self.server_params)
        )
        self.agent: Optional[Agent] = None

    def __enter__(self) -> "MongoDBSearchAgent":
        self.mongo_client.__enter__()
        tools = self.mongo_client.list_tools_sync()

        self.agent = Agent(
            tools=tools,
            system_prompt=f"""
You are {self.name}.
{self.description}

Choose the most appropriate MongoDB Atlas MCP tool for each query.
Use only available tools and never invent database results.

Use database inventory_db for all queries and only use data for the tenant_id in the request context. Never use data from another tenant. If the query is not relevant to the database and tenant, respond with "I cannot answer that question."
""",
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.mongo_client.__exit__(exc_type, exc_value, traceback)
        self.agent = None

    def search(self, query: str, *, tenant_id: str) -> Any:
        if self.agent is None:
            raise RuntimeError("Use MongoDBSearchAgent as a context manager.")

        context = {"tenant_id": tenant_id}
        return self.agent(
            f"Request context: {context}\n\nUser query: {query}",
            invocation_state=context,
        )


# if __name__ == "__main__":
#     with MongoDBSearchAgent() as agent:
#         # Get query from user input
#         user_query = input("Enter your query: ")
#         result = agent.search(user_query)
#         print("Search result:", result)