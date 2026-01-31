from strands import Agent
from tools.athena_tool import run_athena

ATHENA_DATABASE = "demo"
allowed_tables = "sales_transactions"
sales_agent = Agent(
    name="sales_agent",
    system_prompt=f"""
SQL execution agent. Execute queries using run_athena tool.

TABLE: {allowed_tables}
DATABASE: {ATHENA_DATABASE}

Call run_athena, return data. No SQL code shown. No explanations.
""",
    tools=[run_athena],
    tool_choice="required",
)
