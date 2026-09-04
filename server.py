from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent import MongoDBSearchAgent

mongo_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_agent

    with MongoDBSearchAgent() as mongo_agent:
        yield

    mongo_agent = None


app = FastAPI(title="MongoDB Strands Agent", lifespan=lifespan)


class QueryRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/query")
def query(request: QueryRequest):
    if mongo_agent is None:
        raise HTTPException(status_code=503, detail="Agent unavailable")

    with MongoDBSearchAgent() as search_agent:
        agent_result = search_agent.search(request.query)
    
    return {"result": str(agent_result)}