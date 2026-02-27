from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.multiagent import Swarm
import boto3
from datetime import datetime, timezone
import uuid
import logging
import time

from agents.master_agent import master_agent
from agents.clients_agent import clients_agent
from agents.customers_agent import customers_agent
from agents.orders_products_agent import orders_products_agent
from agents.sales_agent import sales_agent
from core.result_extractor import extract_final_answer


# 🔒 Reduce noisy AgentCore logs (optional but recommended)
logging.getLogger("bedrock_agentcore").setLevel(logging.ERROR)
logging.getLogger("bedrock_agentcore.app").setLevel(logging.ERROR)


# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('demo_agent_history')


# Create swarm
swarm = Swarm(
    [
        master_agent,
        clients_agent,
        customers_agent,
        orders_products_agent,
        sales_agent
    ]
)


app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload: dict):
    query = payload.get("prompt", "")

    print("===== INVOKE START =====")
    print("Query:", query)

    try:
        result = swarm.run(query)
        print("Swarm result:", result)
    except Exception as e:
        print("Swarm crashed:", str(e))
        return {
            "final_answer": f"Swarm error: {str(e)}"
        }

    # Force safe conversion
    try:
        final_answer = extract_final_answer(result)
        print("Extracted answer:", final_answer)
    except Exception as e:
        print("Extractor crashed:", str(e))
        final_answer = f"Extractor error: {str(e)}"

    # Guarantee non-null return
    if not final_answer:
        final_answer = "No answer generated."

    print("Returning:", final_answer)
    print("===== INVOKE END =====")

    return {
        "final_answer": str(final_answer)
    }


if __name__ == "__main__":
    app.run()