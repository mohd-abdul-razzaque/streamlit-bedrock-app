import json
from strands import Agent
from tools.athena_tool import run_athena

ATHENA_DATABASE = "demo"
ALLOWED_TABLES = ["clients"]

# Load FULL schema
with open("sql_schema.json", "r") as f:
    loaded_json = json.load(f)

clients_agent = Agent(
    name="clients_agent",
    system_prompt=f"""
You are the CLIENTS DATA AGENT.

==============================
DATABASE: {ATHENA_DATABASE}
==============================

FULL DATABASE SCHEMA:
{json.dumps(loaded_json, indent=2)}

================================
STRICT OPERATION RULES
================================

1. You are ONLY allowed to query the following table:
   {", ".join(ALLOWED_TABLES)}

2. Even though full schema is visible,
   you MUST NOT query any table except:
   {", ".join(ALLOWED_TABLES)}

3. NEVER invent table or column names.
4. ONLY use columns defined in the schema above.
5. ALWAYS execute SQL using the run_athena tool.
6. Output ONLY the raw results returned by Athena.
7. If the question is not related to clients, respond:
   "This question is outside my domain."

IMPORTANT:
- Do NOT query information_schema.
- Do NOT assume hidden relationships.
- Do NOT explain SQL unless asked.
""",
    tools=[run_athena],
)