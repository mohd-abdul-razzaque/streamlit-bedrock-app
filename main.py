from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.multiagent import Swarm
import boto3
from datetime import datetime, timezone
import uuid

from agents.master_agent import master_agent
from agents.clients_agent import clients_agent
from agents.customers_agent import customers_agent
from agents.orders_products_agent import orders_products_agent
from agents.sales_agent import sales_agent
from core.result_extractor import extract_final_answer

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('demo_agent_history')

swarm = Swarm(
    [
        master_agent,
        clients_agent,
        customers_agent,
        orders_products_agent,
        sales_agent
    ],
    max_turns=10,  # Limit conversation turns
)

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload: dict):
    query = payload.get("prompt", "")
    result = swarm(query)
    final_answer = extract_final_answer(result)
    
    # Store question and answer in DynamoDB
    try:
        table.put_item(
            Item={
                'query_id': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'question': query,
                'answer': str(final_answer)
            }
        )
    except Exception as e:
        print(f"Error storing to DynamoDB: {str(e)}")
    
    return final_answer

if __name__ == "__main__":
    app.run()
