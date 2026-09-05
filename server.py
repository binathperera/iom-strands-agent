from contextlib import asynccontextmanager
import os

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dotenv import load_dotenv
from pydantic import BaseModel

from agent import InventoryOperationsManagerAgent

load_dotenv()

mongo_agent = None
bearer_scheme = HTTPBearer(auto_error=False)
JWT_SECRET = os.getenv("JWT_SECRET")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_agent

    with InventoryOperationsManagerAgent() as mongo_agent:
        yield

    mongo_agent = None


app = FastAPI(title="MongoDB Strands Agent", lifespan=lifespan)


class QueryRequest(BaseModel):
    query: str


def get_token_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> tuple[str, str]:
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

    return credentials.credentials, tenant_id


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/query")
def query(
    request: QueryRequest,
    token_context: tuple[str, str] = Depends(get_token_context),
):
    if mongo_agent is None:
        raise HTTPException(status_code=503, detail="Agent unavailable")

    authorization_token, tenant_id = token_context
    with InventoryOperationsManagerAgent(
        authorization_token=authorization_token,
    ) as search_agent:
        agent_result = search_agent.search(
            request.query,
            tenant_id=tenant_id,
        )
    
    return {"result": str(agent_result)}