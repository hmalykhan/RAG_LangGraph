import asyncio, json, sys, websockets

async def main(text):
    async with websockets.connect("ws://localhost:8000/ws/chat/testsession1") as ws:
        await ws.send(json.dumps({"type": "chat:send", "request_id": "r1", "text": text}))
        tokens = 0
        while True:
            msg = json.loads(await ws.recv())
            if msg["type"] == "chat:token":
                tokens += 1
                print(msg["text"], end="", flush=True)
            else:
                print(f"\n[{msg['type']}] {msg}")
            if msg["type"] in ("chat:completed", "chat:error"):
                break
        print(f"\nchat:token messages received: {tokens}")

asyncio.run(main(sys.argv[1]))
