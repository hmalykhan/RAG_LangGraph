import asyncio
from backend.database import init_db
from backend.agents import knowledge_agent, support_agent

CFG = {"configurable": {"session_id": "abc12345"}}

async def ask(agent, text):
    r = await agent.ainvoke({"messages": [("user", text)]}, config=CFG)
    print(r["messages"][-1].content, "\n")

async def main():
    await init_db()
    await ask(knowledge_agent, "Can I return my damaged laptop after 10 days?")
    await ask(knowledge_agent, "What is the price of the X5 laptop?")
    await ask(support_agent, "My order 1042 arrived damaged. Open a complaint.")

asyncio.run(main())
