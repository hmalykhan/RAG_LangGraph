from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from backend.vector_store import vstore
from backend.database import (
    insert_ticket, fetch_ticket, set_ticket_status, VALID_STATUSES,
)


@tool
async def search_knowledge(question: str) -> str:
    """Search the company policy documents (returns, shipping, warranty).
    Returns the top matching text chunks with their source filenames.
    Use this for any policy question."""
    import asyncio
    docs = await asyncio.to_thread(vstore.similarity_search, question, 3)
    if not docs:
        return "NO_RELEVANT_SOURCES"
    return "\n\n".join(
        f"[source: {d.metadata.get('source', 'unknown')}]\n{d.page_content}"
        for d in docs
    )


@tool
async def create_ticket(order_id: str, complaint: str, config: RunnableConfig) -> str:
    """Create a new support ticket for an order complaint.
    Needs the order ID and a short description of the complaint.
    Returns the real saved ticket ID."""
    session_id = config["configurable"]["session_id"]
    t = await insert_ticket(session_id, order_id, complaint)
    return f"Ticket created. ID={t.id}, order_id={t.order_id}, status={t.status}"


@tool
async def get_ticket(ticket_id: int) -> str:
    """Get the current status of a support ticket by its numeric ID."""
    t = await fetch_ticket(ticket_id)
    if not t:
        return f"Ticket {ticket_id} was not found."
    return (f"Ticket ID={t.id}, order_id={t.order_id}, "
            f"issue={t.description}, status={t.status}")


@tool
async def update_ticket(ticket_id: int, status: str) -> str:
    """Update a ticket's status. Allowed values: OPEN, IN_REVIEW, RESOLVED."""
    status = status.strip().upper()
    if status not in VALID_STATUSES:
        return f"Invalid status '{status}'. Allowed: OPEN, IN_REVIEW, RESOLVED."
    t = await set_ticket_status(ticket_id, status)
    if not t:
        return f"Ticket {ticket_id} was not found."
    return f"Ticket ID={t.id} updated. New status={t.status}"
