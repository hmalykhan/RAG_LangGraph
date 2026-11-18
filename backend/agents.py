import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent

from backend.tools import search_knowledge, create_ticket, get_ticket, update_ticket

load_dotenv()

llm = ChatGroq(model=os.getenv("GROQ_MODEL"), temperature=0, streaming=True)

KNOWLEDGE_PROMPT = (
    "You are the Knowledge Agent for a customer support chatbot. "
    "Always call search_knowledge first, then answer ONLY from its results. "
    "Always cite the source filename, for example (source: return_policy.txt). "
    "If the results are empty or not relevant, say you do not have that "
    "information. Never invent policies, prices, or stock amounts."
)

SUPPORT_PROMPT = (
    "You are the Support Agent for a customer support chatbot. "
    "Use create_ticket to open complaints (you need an order ID and a "
    "complaint description; ask the user if the order ID is missing). "
    "Use get_ticket to check status and update_ticket to change status. "
    "Never state a ticket ID or status that a tool did not return. "
    "When the user says 'it' or 'its status', find the ticket ID in the "
    "earlier conversation messages. Always include the real ticket ID "
    "from the tool result in your reply."
)

knowledge_agent = create_agent(llm, tools=[search_knowledge], system_prompt=KNOWLEDGE_PROMPT)
support_agent = create_agent(
    llm,
    tools=[create_ticket, get_ticket, update_ticket],
    system_prompt=SUPPORT_PROMPT,
)
