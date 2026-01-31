from strands import Agent
from tools.athena_tool import run_athena

ATHENA_DATABASE = "demo"
allowed_tables = "clients"

clients_agent = Agent(
    name="clients_agent",
    system_prompt=f"""
USE run_athena TOOL FOR EVERY QUESTION.

TABLE: {allowed_tables}
DATABASE: {ATHENA_DATABASE}

FORBIDDEN: Showing SQL, explanations
REQUIRED: Call run_athena, return data
""",
    tools=[run_athena],
)