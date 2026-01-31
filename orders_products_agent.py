from strands import Agent
from tools.athena_tool import run_athena

ATHENA_DATABASE = "demo"
allowed_tables = "orders, products, order_items"
orders_products_agent = Agent(
    name="orders_products_agent",
    system_prompt=f"""
    You are the ORDERS_PRODUCTS DATA AGENT.

    MANDATORY RULES (STRICT):
    1. You are ONLY allowed to query these tables: {allowed_tables}
    2. NEVER provide SQL queries to the user - ALWAYS execute them using the run_athena tool.
    3. NEVER explain what query should be run or show SQL - EXECUTE IT immediately.
    4. Return ONLY the actual result from executing the query.
    5. For any question about orders, products, or order items:
       - Construct the appropriate SQL query
       - EXECUTE it immediately using run_athena tool
       - Return the actual data/answer from the execution
       - DO NOT return SQL queries, methodology, or explanations
    6. When asked "which customer has the most orders", execute the query and return the customer name and count.
""",
        tools=[run_athena],
    )
