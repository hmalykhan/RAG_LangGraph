SUPPORT_KEYWORDS = [
    "ticket", "complaint", "status", "open a", "arrived damaged",
    "update", "resolve", "resolved", "in review",
]
KNOWLEDGE_KEYWORDS = [
    "return", "refund", "shipping", "delivery", "deliver", "warranty",
    "policy", "damage", "water", "dispatch", "tracking",
]


def route(text: str, history: list | None = None) -> str | None:
    t = text.lower()
    if any(k in t for k in SUPPORT_KEYWORDS):
        return "support"
    if any(k in t for k in KNOWLEDGE_KEYWORDS):
        return "knowledge"
    return None  # caller asks a short clarifying question
