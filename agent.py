import os
from typing import Any, Optional

from mcp.client.stdio import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient


class InventoryOperationsManagerAgent:
    """Strands agent using Local MongoDB MCP tools via Stdio and remote inventory MCP server."""

    def __init__(
        self,
        name: str = "inventory-operations-manager-agent",
        description: str = "Searches MongoDB Atlas using natural-language queries and executes user commands.",
        authorization_token: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.authorization_token = authorization_token

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
        self.java_mcp_client = None
        if authorization_token:
            java_mcp_url = os.getenv("JAVA_MCP_URL", "http://localhost/mcp")
            self.java_mcp_client = MCPClient(
                url=java_mcp_url,
                headers={"Authorization": f"Bearer {authorization_token}"},
                prefix="java",
            )
        self.agent: Optional[Agent] = None

    def __enter__(self) -> "InventoryOperationsManagerAgent":
        self.mongo_client.__enter__()
        tools = self.mongo_client.list_tools_sync()
        if self.java_mcp_client is not None:
            self.java_mcp_client.__enter__()
            tools += self.java_mcp_client.list_tools_sync()

        self.agent = Agent(
            tools=tools,
            system_prompt=f"""
You are {self.name}.
{self.description} 

Choose the most appropriate tool from the MongoDB Atlas or Java inventory MCP servers for each query.
Use only available tools and never invent database results.

Use the mongoDB mcp server only for searching. When using mongoDB mcp server, use database inventory_db for all queries and only use data for the tenant_id in the request context. Never use data from another tenant. If the query is not relevant to the database and tenant, respond with "I cannot answer that question.".
For other actions such as performing additions, updates and deletions use the Java inventory MCP server. If the tools do not provide the functionality needed, respond with "I cannot perform that action.".
""",
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.java_mcp_client is not None:
            self.java_mcp_client.__exit__(exc_type, exc_value, traceback)
        self.mongo_client.__exit__(exc_type, exc_value, traceback)
        self.agent = None

    def search(self, query: str, *, tenant_id: str) -> Any:
        if self.agent is None:
            raise RuntimeError("Use InventoryOperationsManagerAgent as a context manager.")

        context = {"tenant_id": tenant_id}
        return self.agent(
            f"Request context: {context}\n\nUser query: {query}",
            invocation_state=context,
        )


# if __name__ == "__main__":
#     with InventoryOperationsManagerAgent() as agent:
#         # Get query from user input
#         user_query = input("Enter your query: ")
#         result = agent.search(user_query)
#         print("Search result:", result)