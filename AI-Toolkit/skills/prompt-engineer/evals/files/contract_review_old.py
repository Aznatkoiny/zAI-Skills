SYSTEM = """You are ContractBot. CRITICAL: You MUST ALWAYS use the search_clause_db tool for EVERY clause, no exceptions!!! If in doubt, search.
NEVER use markdown. NEVER use bullet points.
Think step by step inside <thinking> tags before answering, and show your full reasoning to the user so they can audit it.
Return a JSON object {\"risk_level\": \"low|medium|high\", \"issues\": [...]}."""

resp = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4000,
    system=SYSTEM,
    thinking={"type": "enabled", "budget_tokens": 3000},
    tools=[search_clause_db],
    messages=[
        {"role": "user", "content": f"Review this contract:\n{contract_text}\n\nWhat are the risks?"},
        {"role": "assistant", "content": "{\"risk_level\": \""}
    ],
)
result = json.loads('{"risk_level": "' + resp.content[0].text)
