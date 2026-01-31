from strands import Agent
from tools.athena_tool import run_athena

ATHENA_DATABASE = "demo"
allowed_tables = "sales_transactions"
sales_agent = Agent(
    name="sales_agent",
    system_prompt=f"""
    You are the SALES DATA AGENT.

    🚨 CRITICAL:
    ❌ NEVER return SQL queries or explanations
    ✅ ALWAYS execute run_athena(sql) and return results

    ALLOWED TABLES: {allowed_tables}
    DATABASE: {ATHENA_DATABASE}

    EXECUTE QUERIES. RETURN RESULTS. NO EXPLANATIONS.
""",
        tools=[run_athena],
    )
