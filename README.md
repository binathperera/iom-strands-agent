# Inventory Operations Manager Agent

FastAPI service for querying inventory data with natural-language requests. The
service uses the AWS Strands Agents SDK and connects to inventory tools through
Model Context Protocol (MCP) servers.

## Features

- Health check endpoint for service monitoring.
- JWT bearer-token authentication for inventory queries.
- Tenant and role context passed to the agent for each request.
- Read-only MongoDB MCP access for inventory searches.
- Java inventory MCP access for inventory actions when configured.

## Requirements

- Python 3.12 or later
- Node.js and `npx` for the MongoDB MCP server
- Access to an AWS model provider supported by the Strands Agents SDK
- A MongoDB connection string
- A Java inventory MCP server for action requests

The Dockerfile installs Node.js and `mongodb-mcp-server` automatically. For local development, install the MongoDB MCP package with npm if it is not already available:

```powershell
npm install --global mongodb-mcp-server
```

## Configuration

Create a local `.env` file. Do not commit it or share its contents.

```dotenv
AWS_ACCESS_KEY_ID=<your-aws-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-access-key>
AWS_REGION=<your-aws-region>
MONGODB_URI=<your-mongodb-connection-string>
JWT_SECRET=<your-jwt-signing-secret>
INVENTORY_MCP_URL=http://localhost:8080/mcp
```

| Variable | Required | Description |
| --- | --- | --- |
| `AWS_ACCESS_KEY_ID` | Yes | AWS credentials used by the configured Strands model provider. |
| `AWS_SECRET_ACCESS_KEY` | Yes | AWS secret key used by the configured Strands model provider. |
| `AWS_REGION` | Yes | AWS region for the configured model provider. |
| `MONGODB_URI` | Yes | MongoDB connection string passed to the MongoDB MCP server. |
| `JWT_SECRET` | Yes | Secret used to validate HS256 bearer tokens. |
| `INVENTORY_MCP_URL` | No | Inventory MCP endpoint. Defaults to `http://localhost:8080/mcp`. |
| `MCP_COMMAND` | No | MCP executable. Defaults to `npx.cmd` on Windows and `npx` elsewhere. |

The application loads `.env` during startup. Environment variables already set
by the operating system take precedence over values in `.env`.

## Installation

Create and activate a virtual environment, then install the Python dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Running Locally

Start the API with:

```powershell
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

The interactive API documentation is available at
`http://127.0.0.1:8000/docs`.

## Running with Docker

Build and run the image:

```powershell
docker build -t inventory-operations-manager-agent .
docker run --rm -p 8000:8000 --env-file .env inventory-operations-manager-agent
```

The container listens on port `8000`.

## API Endpoints

### `GET /health`

Returns the service status:

```json
{
	"status": "healthy"
}
```

### `POST /query`

Requires an `Authorization` header containing a JWT bearer token. The token
must use the HS256 algorithm and include a non-empty `tenantId` claim. The
optional `roles` claim must be a list.

Request:

```http
POST /query HTTP/1.1
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
	"query": "Find the available stock for product ABC"
}
```

Successful response:

```json
{
	"result": "<agent response>"
}
```

Common errors include `401` for missing or invalid authentication,
`503` when the agent is unavailable, and `500` when `JWT_SECRET` is not
configured.

## Security Notes

- Never commit `.env` files, cloud credentials, database credentials, or JWT secrets.
- Rotate credentials immediately if they are exposed.
- Use a strong, randomly generated `JWT_SECRET` in each environment.
- Use read-only MongoDB permissions where search-only access is sufficient.
- Configure CORS, TLS, and deployment-level access controls before exposing the API publicly.

## Project Files

- `server.py`: FastAPI application, lifespan management, authentication, and routes.
- `agent.py`: Strands agent and MCP client configuration.
- `requirements.txt`: Python dependencies.
- `Dockerfile`: Container build and startup configuration.