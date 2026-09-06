# Description: Server code for the Inventory Operations Manager Agent FastAPI application.
# Configuration:
#              See README.md for required environment variables.

from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from agent import InventoryOperationsManagerAgent

load_dotenv() #In case you want to use a .env file for local development, this will load the environment variables from it.

mongo_agent = None # Global variable to hold the InventoryOperationsManagerAgent instance
bearer_scheme = HTTPBearer(auto_error=False) # Define the HTTP Bearer authentication scheme
JWT_SECRET = os.getenv("JWT_SECRET") # Load the JWT secret from environment variables

#Define a lifespan context manager for the FastAPI application 
#to manage the lifecycle behaviour of the application
@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_agent
    # Initialize the InventoryOperationsManagerAgent
    with InventoryOperationsManagerAgent() as mongo_agent:
        # The agent is now available for handling requests
        yield 
    mongo_agent = None # Clean up the InventoryOperationsManagerAgent instance when the application shuts down

app = FastAPI(title="Inventory Operations Manager Agent", lifespan=lifespan)

#define a Pydantic model for the query request
class QueryRequest(BaseModel):
    query: str #query will be a string containing the natural language query to be processed by the agent

#Define a dependency function to extract and validate the JWT token from the request headers
def get_token_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> tuple[str, str, list[str]]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Bearer token is required")
    if not JWT_SECRET:
        raise HTTPException(status_code=500, detail="JWT_SECRET is not configured")

    try:
        claims = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=["HS256"],
        )
    except jwt.InvalidTokenError as error:
        raise HTTPException(status_code=401, detail="Invalid bearer token") from error

    tenant_id = claims.get("tenantId")
    if not isinstance(tenant_id, str) or not tenant_id:
        raise HTTPException(status_code=401, detail="Token is missing tenant id")

    roles = claims.get("roles", [])
    if not isinstance(roles, list):
        roles = []

    return credentials.credentials, tenant_id, roles

# API endpoint definitions for the FastAPI application
# <100: Not used
# 1xx: Informational Responses
# 2xx: Successful Responses
# 3xx: Redirection Messages
# 4xx: Client Error Responses
# 5xx: Server Error Responses
# 600-999: Not used

# Define a health check endpoint to verify that the application is running
@app.get("/health")
def health():
    return {"status": "healthy"}

# Define a query endpoint to process natural language queries using the InventoryOperationsManagerAgent
@app.post("/query")
def query(
    request: QueryRequest,
    token_context: tuple[str, str, list[str]] = Depends(get_token_context),
):
    if mongo_agent is None:
        raise HTTPException(status_code=503, detail="Agent unavailable")

    authorization_token, tenant_id, roles = token_context
    with InventoryOperationsManagerAgent(
        authorization_token=authorization_token,
    ) as search_agent:
        agent_result = search_agent.search(
            request.query,
            tenant_id=tenant_id,
            roles=roles,
        )
    
    return {"result": str(agent_result)}