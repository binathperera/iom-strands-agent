Inventory Operations Manager Agent

This agent is developed using the AWS strands sdk to help business owners manage inventory.

Agent Tools,
1. MongoDB MCP Tools- Connects to local MCP MongoDB Server which requires npx

To run the agent server,
python -m uvicorn server:app --host 127.0.0.1 --port 8000