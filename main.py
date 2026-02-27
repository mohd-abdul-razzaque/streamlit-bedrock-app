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

    print("\n===== INVOKE CALLED =====")
    print("Query:", query)

    try:
        result = swarm.run(query)
    except Exception as e:
        print("Swarm error:", str(e))
        return {
            "final_answer": f"Swarm error: {str(e)}"
        }

    print("\n===== RAW SWARM RESULT =====")
    print(result)
    print("TYPE:", type(result))
    print("============================\n")

    # FORCE non-null return no matter what
    if result is None:
        return {
            "final_answer": "Swarm returned None."
        }

    return {
        "final_answer": str(result)
    }


if __name__ == "__main__":
    app.run()