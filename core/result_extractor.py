def extract_final_answer(swarm_result):
    """
    Production-safe extractor for Strands SwarmResult.
    Always returns the latest assistant text available.
    Never returns None.
    """

    if not swarm_result:
        return "No result returned from swarm."

    # Return only explicit final answers
    if isinstance(swarm_result, dict):
        final_answer = swarm_result.get("final_answer")
        if isinstance(final_answer, str) and final_answer.strip():
            return final_answer.strip()

    final = getattr(swarm_result, "final", None)
    if isinstance(final, str) and final.strip():
        return final.strip()

    return "Final answer not available yet."