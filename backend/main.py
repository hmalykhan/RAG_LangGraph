import asyncio
import logging
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.database import (
    init_db, load_messages, save_message, fetch_ticket,
    list_documents_db, upsert_document,
)
from backend.ingest import ingest_text
from backend.router import route
from backend.agents import knowledge_agent, support_agent

logger = logging.getLogger("chat")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from backend.vector_store import vstore
    await asyncio.to_thread(vstore.similarity_search, "warmup", 1)
    yield


app = FastAPI(title="Class 04 AI Support", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 1. POST /api/documents/upload
@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")
    text = (await file.read()).decode("utf-8")
    chunks = await asyncio.to_thread(ingest_text, file.filename, text)
    await upsert_document(file.filename, chunks)
    return {"filename": file.filename, "chunks": chunks}


# 2. GET /api/documents
@app.get("/api/documents")
async def list_documents():
    docs = await list_documents_db()
    return [
        {"filename": d.filename, "chunk_count": d.chunk_count,
         "uploaded_at": d.uploaded_at.isoformat()}
        for d in docs
    ]


# 3. GET /api/tickets/{ticket_id}
@app.get("/api/tickets/{ticket_id}")
async def get_ticket_http(ticket_id: int):
    t = await fetch_ticket(ticket_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"id": t.id, "order_id": t.order_id,
            "issue": t.description, "status": t.status}


# 4. GET /api/conversations/{session_id}/messages
@app.get("/api/conversations/{session_id}/messages")
async def get_messages(session_id: str):
    msgs = await load_messages(session_id)
    return [
        {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in msgs
    ]


# 5. WS /ws/chat/{session_id}
@app.websocket("/ws/chat/{session_id}")
async def chat_ws(ws: WebSocket, session_id: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", session_id):
        await ws.close(code=1008)
        return
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            rid = data.get("request_id")
            text = (data.get("text") or "").strip()

            if data.get("type") != "chat:send" or not rid or not text:
                await ws.send_json({"type": "chat:error", "request_id": rid,
                                    "message": "Invalid message"})
                continue

            try:
                history = await load_messages(session_id)
                await save_message(session_id, "user", text)

                which = route(text, history)
                if which is None:
                    msg = ("Is your question about a return/shipping/warranty "
                           "policy, or about a support ticket?")
                    await ws.send_json({"type": "chat:token", "request_id": rid, "text": msg})
                    await save_message(session_id, "assistant", msg)
                    await ws.send_json({"type": "chat:completed", "request_id": rid})
                    continue

                await ws.send_json({"type": "agent:selected", "request_id": rid, "agent": which})
                agent = knowledge_agent if which == "knowledge" else support_agent

                messages = [(m.role, m.content) for m in history] + [("user", text)]
                final = ""

                async for ev in agent.astream_events(
                    {"messages": messages},
                    config={"configurable": {"session_id": session_id}},
                    version="v2",
                ):
                    kind = ev["event"]
                    if kind == "on_tool_start":
                        await ws.send_json({"type": "tool:started", "request_id": rid,
                                            "tool": ev["name"]})
                    elif kind == "on_tool_end":
                        await ws.send_json({"type": "tool:completed", "request_id": rid,
                                            "tool": ev["name"]})
                    elif kind == "on_chat_model_stream":
                        chunk = ev["data"]["chunk"]
                        if chunk.content and not chunk.tool_call_chunks:
                            final += chunk.content
                            await ws.send_json({"type": "chat:token", "request_id": rid,
                                                "text": chunk.content})

                await save_message(session_id, "assistant", final)
                await ws.send_json({"type": "chat:completed", "request_id": rid})
            except Exception as e:
                logger.exception("chat failed")
                await ws.send_json({"type": "chat:error", "request_id": rid, "message": str(e)})
    except WebSocketDisconnect:
        pass
