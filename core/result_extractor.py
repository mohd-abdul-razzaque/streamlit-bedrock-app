def extract_final_answer(swarm_result):
    """
    Robust extraction of final answer from Strands SwarmResult.
    Always returns a string.
    """

    if not swarm_result:
        return "No result returned from swarm."

    # Case 1: No results attribute
    if not hasattr(swarm_result, "results"):
        return str(swarm_result)

    answers = []

    for node_name, node_result in swarm_result.results.items():
        result = getattr(node_result, "result", None)
        if not result:
            continue

        message = getattr(result, "message", None)
        if not message:
            continue

        content = message.get("content", [])

        for item in content:
            if isinstance(item, dict) and "text" in item:
                text = item["text"].strip()
                if text:
                    answers.append(text)

    # Return last meaningful answer
    if answers:
        return answers[-1]

    # Fallback for debugging
    return "Swarm completed but no final answer was extracted."