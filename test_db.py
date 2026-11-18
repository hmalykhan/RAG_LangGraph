import asyncio
from backend.database import init_db, insert_ticket, save_message

async def main():
    await init_db()
    t = await insert_ticket("abc12345", "1042", "Laptop arrived damaged")
    print("ticket id:", t.id, t.status)
    await save_message("abc12345", "user", "hello")
    await save_message("abc12345", "assistant", "hi there")

asyncio.run(main())
