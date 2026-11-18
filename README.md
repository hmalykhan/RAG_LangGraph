# Real-Time AI Knowledge and Support System

A localhost prototype of an AI customer-support chatbot with **two agents**, **four tools**, and **real token streaming** over a native WebSocket. Customers ask policy questions (answered from company documents via RAG) or ask the bot to create, check, and update support tickets stored in SQLite.

> Demo only: no login, fictional data, run on localhost. A session ID is **not** authentication.

## Description

The system combines Retrieval-Augmented Generation (RAG) with tool-calling agents:

- The **Knowledge Agent** answers returns, shipping, and warranty questions using only text retrieved from Astra DB, cites the source filename, and says so when information is missing.
- The **Support Agent** creates complaint tickets, reads ticket status, and updates status (`OPEN`, `IN_REVIEW`, `RESOLVED`) using real SQLite records.
- A simple deterministic **router** picks the agent for each message (no LangGraph workflow).
- Groq's tokens are forwarded to the browser as they are generated, as repeated `chat:token` WebSocket messages.
- LangSmith records an execution trace of every run.

## Technologies

| Area | Technology |
|---|---|
| Language | Python 3.11 |
| Web framework | FastAPI, Uvicorn |
| Real-time transport | Native WebSockets (no Socket.IO) |
| LLM | Groq via LangChain `ChatGroq` (`openai/gpt-oss-120b`, tool calling + streaming) |
| Agent framework | LangChain (`create_agent`, `@tool`) |
| Embeddings | Hugging Face `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) |
| Vector database | DataStax Astra DB (`langchain-astradb`) |
| Relational database | SQLite with SQLAlchemy (async) and aiosqlite |
| Text chunking | `langchain-text-splitters` (RecursiveCharacterTextSplitter) |
| Observability | LangSmith tracing |
| Config | python-dotenv, Pydantic |
| Testing | pytest, httpx, websockets |
| Frontend | Plain HTML, CSS, and JavaScript (WebSocket + Fetch API) |

## Skills Demonstrated

- Retrieval-Augmented Generation: chunking, embedding, vector search, grounded answers with citations
- LLM tool calling and multi-agent design (two agents, four tools)
- Intent routing between agents
- Real-time streaming with async WebSockets (`astream_events`)
- Async Python: `asyncio`, `asyncio.to_thread` for blocking calls, async SQLAlchemy
- REST API design with FastAPI (uploads, reads, 404 handling)
- Conversation memory and persistence in SQLite
- Hallucination control through strict system prompts and "no source, no answer" behavior
- LLM observability and tracing with LangSmith
- Secrets management with `.env` and `.env.example`
- Automated testing with pytest

## Architecture

```
Browser (HTML/JS)
   |  HTTP: upload, list docs, ticket read, history
   |  WebSocket: chat:send  ->  agent:selected, tool:started/completed, chat:token, chat:completed
   v
FastAPI (main.py)
   |-- router.py        picks Knowledge or Support agent
   |-- agents.py        LangChain agents on Groq
   |-- tools.py         search_knowledge, create_ticket, get_ticket, update_ticket
   |-- vector_store.py  Hugging Face embeddings + Astra DB
   |-- ingest.py        TXT chunking + indexing
   |-- database.py      SQLite: conversations, messages, tickets, documents
```

- **Astra DB** stores document embeddings and chunk text for search.
- **SQLite** stores tickets, chat history, and document metadata.
- **Groq** generates answers but can only change data by calling the Python tools.

## Project Structure

```
class04-ai-support/
  frontend/index.html     chat + document upload UI
  backend/
    main.py               4 HTTP routes + 1 WebSocket
    router.py             chooses 1 of 2 agents
    agents.py             Knowledge + Support agents
    tools.py              the 4 tools
    vector_store.py       HF embeddings + Astra DB
    ingest.py             chunking + indexing
    database.py           SQLite models + helpers
  data/                   return_policy.txt, shipping_policy.txt, product_faq.txt
  .env.example            variable names only
  requirements.txt
  README.md
```

## Setup

1. Create the environment and install dependencies:
   ```bash
   conda create -n rag python=3.11 -y
   conda activate rag
   pip install -r requirements.txt
   pip install greenlet
   ```
2. Pre-download the embedding model:
   ```bash
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
   ```
3. Copy `.env.example` to `.env` and fill in your keys:
   ```
   GROQ_API_KEY=
   GROQ_MODEL=openai/gpt-oss-120b
   ASTRA_DB_API_ENDPOINT=
   ASTRA_DB_APPLICATION_TOKEN=
   ASTRA_DB_COLLECTION=support_kb
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=
   LANGSMITH_PROJECT=class04-support
   DATABASE_URL=sqlite+aiosqlite:///./support.db
   ```
   Never commit `.env`.
4. Start the backend:
   ```bash
   uvicorn backend.main:app --reload
   ```
5. Serve the frontend in a second terminal:
   ```bash
   cd frontend && python -m http.server 5500
   ```
   Open http://localhost:5500.
6. Upload the three files in `data/` using the Documents panel, then start chatting.

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/documents/upload` | Upload a `.txt`, chunk, embed, store in Astra DB, return filename + chunk count (re-upload replaces old chunks) |
| GET | `/api/documents` | List indexed files, chunk counts, upload timestamps |
| GET | `/api/tickets/{ticket_id}` | Read a ticket from SQLite, or 404 |
| GET | `/api/conversations/{session_id}/messages` | Saved messages in chronological order |
| WS | `/ws/chat/{session_id}` | Chat. Client sends `chat:send`; server sends `agent:selected`, `tool:started`, `tool:completed`, `chat:token`, `chat:completed`, `chat:error` |

## Request Flow: what happens when the user clicks Send

1. The frontend creates a `request_id`, shows the user message, and sends `{type: "chat:send", request_id, text}` over the open WebSocket.
2. FastAPI receives the JSON and validates the type, `request_id`, and text.
3. SQLite provides the earlier messages saved under the same session ID.
4. The user message is saved exactly once.
5. The router chooses the Knowledge Agent or Support Agent (or asks a clarifying question).
6. FastAPI sends `agent:selected` so the UI can show which agent is working.
7. The LangChain agent runs on Groq with its allowed tools; `tool:started` and `tool:completed` are sent for each tool call.
8. For policy questions, `search_knowledge` embeds the question with Hugging Face and Astra DB returns the top 3 chunks with filenames.
9. For tickets, the Support Agent calls `create_ticket`, `get_ticket`, or `update_ticket`, which read and write SQLite.
10. As Groq generates the answer, each text piece is forwarded immediately as a `chat:token` message.
11. The browser appends each piece to the AI chat bubble while the answer is generated.
12. The final answer is saved in SQLite and `chat:completed` is sent.
13. LangSmith records the full execution trace. On any failure, `chat:error` is sent and the error is logged.

## Demo Prompts

1. `Can I return my damaged laptop after 10 days?` uses the Knowledge Agent and cites `return_policy.txt`.
2. `My order 1042 arrived damaged. Open a complaint.` uses the Support Agent and creates a real ticket.
3. `What is its status?` uses saved memory to find the ticket and read its latest status.

Negative test: `What is the price of the X5 laptop?` should say the information is not available, with no invented price.

## Proving Real Streaming

Open browser DevTools, go to Network, WS, Messages, and send a question. Many separate `chat:token` frames arrive while the model generates. Add your screenshots here:

- `docs/ws-tokens.png`
- `docs/langsmith-trace.png`

## Tests

```bash
pytest test_router.py -q
python test_ws.py "Can I return my damaged laptop after 10 days?"
```

## Limitations

- No authentication; session IDs are not proof of identity.
- Keyword router; ambiguous messages get a clarifying question.
- Fictional data and localhost only. Do not deploy as an open service or use private customer information.
