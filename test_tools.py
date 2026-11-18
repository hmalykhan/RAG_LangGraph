import asyncio
from backend.database import init_db
from backend.tools import search_knowledge, create_ticket, get_ticket, update_ticket

CFG = {"configurable": {"session_id": "abc12345"}}

async def main():
    await init_db()
    print("--- search ---")
    print((await search_knowledge.ainvoke({"question": "damaged laptop return"}))[:300])
    print("--- create ---")
    print(await create_ticket.ainvoke({"order_id": "1042", "complaint": "Arrived damaged"}, config=CFG))
    print("--- get ---")
    print(await get_ticket.ainvoke({"ticket_id": 1}))
    print("--- get missing ---")
    print(await get_ticket.ainvoke({"ticket_id": 9999}))
    print("--- update ok ---")
    print(await update_ticket.ainvoke({"ticket_id": 1, "status": "IN_REVIEW"}))
    print("--- update bad status ---")
    print(await update_ticket.ainvoke({"ticket_id": 1, "status": "BANANA"}))

asyncio.run(main())
