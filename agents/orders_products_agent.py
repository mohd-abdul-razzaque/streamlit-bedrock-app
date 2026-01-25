from strands import Agent
from tools.athena_tool import run_athena

ATHENA_DATABASE = "demo"
allowed_tables = "orders, products, order_items"
orders_products_agent = Agent(
    name="orders_products_agent",
    system_prompt=f"""
    You are the ORDERS_PRODUCTS DATA AGENT.

    MANDATORY RULES (STRICT):
    1. FIRST action in every conversation:
    Execute:
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = '{ATHENA_DATABASE}'
    ORDER BY table_name, ordinal_position;

    2. You are ONLY allowed to query these tables:
    {allowed_tables}

    3. NEVER hallucinate column or table names.
    4. ALWAYS execute SQL using the run_athena tool.
    5. Output ONLY results returned by Athena.
""",
        tools=[run_athena],
    )
