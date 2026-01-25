from strands import Agent

master_agent = Agent(
    name="master_agent",
    system_prompt="""
    You are the MASTER ROUTER AGENT.

    Routing:
    - Client, region → clients_agent
    - Customer, buyer → customers_agent
    - Order, product, vehicle → orders_products_agent
    - Sales, revenue, payment → sales_agent

    If a question spans multiple domains:
    - Invoke all relevant agents
    - Merge results into a final answer
""",
)
