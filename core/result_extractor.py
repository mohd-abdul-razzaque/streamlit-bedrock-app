def extract_final_answer(swarm_result):
    """
    Production-safe extractor for Strands SwarmResult.
    Always returns the latest assistant text available.
    Never returns None.
    """

    if not swarm_result:
        return "No result returned from swarm."

    collected = []

    # 1️⃣ Try standard results dictionary
    results = getattr(swarm_result, "results", {})
    for node_result in results.values():
        result = getattr(node_result, "result", None)
        if not result:
            continue

        message = getattr(result, "message", None)
        if not message:
            continue

        content = message.get("content", [])
        for item in content:
            if isinstance(item, dict) and item.get("text"):
                collected.append(item["text"].strip())

    # 2️⃣ Try top-level messages (some swarm versions store here)
    messages = getattr(swarm_result, "messages", [])
    for msg in messages:
        if msg.get("role") == "assistant":
            for item in msg.get("content", []):
                if isinstance(item, dict) and item.get("text"):
                    collected.append(item["text"].strip())

    # 3️⃣ Try final attribute (newer versions)
    final = getattr(swarm_result, "final", None)
    if isinstance(final, str) and final.strip():
        collected.append(final.strip())

    # 4️⃣ Return last meaningful assistant message
    if collected:
        return collected[-1]

    # 5️⃣ Absolute fallback (debug visibility)
    return f"No assistant text found. Raw result: {str(swarm_result)}"