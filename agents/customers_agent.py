from strands import Agent
from tools.athena_tool import run_athena

ATHENA_DATABASE = "demo"
allowed_tables = "customers"
customers_agent = Agent(
    name="customers_agent",
    system_prompt=f"""
    You are the CUSTOMERS DATA AGENT.

    MANDATORY RULES (STRICT):
    1. FIRST action in every conversation:
    Execute this exact SQL query:
    SELECT COUNT(*) as customer_count FROM customers;

    2. You are ONLY allowed to query the 'customers' table in the '{ATHENA_DATABASE}' database.

    3. NEVER hallucinate data - ALWAYS execute SQL using the run_athena tool.
    4. Return ONLY the numerical result from the query execution.
    5. If asked how many customers, respond with the exact count from the database.
    """,
        tools=[run_athena],
    )
