import time
import boto3
from strands import tool

ATHENA_REGION = "ap-south-1"
ATHENA_DATABASE = "demo"
ATHENA_OUTPUT = "s3://s3-bucket-demo-athena-result/query_result/"

athena = boto3.client("athena", region_name=ATHENA_REGION)


@tool
def run_athena(sql: str):
    """
    Execute Athena SQL and return rows as list[dict].
    """
    print(f"[ATHENA] {sql}")

    qid = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": ATHENA_DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT},
    )["QueryExecutionId"]

    while True:
        status = athena.get_query_execution(QueryExecutionId=qid)
        state = status["QueryExecution"]["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)

    if state != "SUCCEEDED":
        raise RuntimeError(f"Athena query failed: {state}")

    result = athena.get_query_results(QueryExecutionId=qid)
    rows = result["ResultSet"]["Rows"]

    headers = [c["VarCharValue"] for c in rows[0]["Data"]]
    return [
        dict(zip(headers, [d.get("VarCharValue") for d in r["Data"]]))
        for r in rows[1:]
    ]
