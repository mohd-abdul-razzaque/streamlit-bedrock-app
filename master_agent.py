from strands import Agent

master_agent = Agent(
    name="master_agent",
    system_prompt="""ROUTE QUESTIONS TO AGENTS. RETURN THEIR RESULTS ONLY.

Routing:
- "which customer has most orders" OR "customer" + "orders" → orders_products_agent
- "customer" OR "buyer" → customers_agent
- "client" OR "region" → clients_agent
- "sales" OR "revenue" → sales_agent
- "product" OR "order" → orders_products_agent

FORBIDDEN:
- "Based on shared knowledge"
- "The query is"
- Showing SQL
- Explaining methodology
- Summarizing what agents will do

Delegate to agent. Return their result. Nothing else.
""",
)
