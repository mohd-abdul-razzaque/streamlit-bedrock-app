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

    start_time = time.time()

    try:
        result = swarm.run(query)

        print("\n========== RAW SWARM RESULT ==========")
        print(result)
        print("TYPE:", type(result))
        print("DIR:", dir(result))

        messages = getattr(result, "messages", None)
        print("MESSAGES:", messages)
        print("======================================\n")

    except AttributeError:
        result = swarm.invoke(query)

        print("\n========== RAW SWARM RESULT (invoke fallback) ==========")
        print(result)
        print("TYPE:", type(result))
        print("DIR:", dir(result))

        messages = getattr(result, "messages", None)
        print("MESSAGES:", messages)
        print("========================================================\n")

    execution_time = time.time() - start_time
    print(f"Swarm execution time: {execution_time:.2f} seconds")

    # 🔥 TEMPORARY: bypass extractor to inspect raw result
    final_answer = str(result)

    return {
        "final_answer": final_answer
    }


if __name__ == "__main__":
    app.run()