
def extract_final_answer(swarm_result):
    """
    Extract the final user-facing answer from a Strands SwarmResult.
    """
    if not hasattr(swarm_result, "results"):
        return None

    answers = []

    for node_result in swarm_result.results.values():
        result = getattr(node_result, "result", None)
        if not result:
            continue

        message = getattr(result, "message", None)
        if not message:
            continue

        for item in message.get("content", []):
            if isinstance(item, dict) and "text" in item:
                answers.append(item["text"])

    return answers[-1] if answers else None