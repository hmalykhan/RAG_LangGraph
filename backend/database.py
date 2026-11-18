import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import String, Integer, Text, DateTime, select, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./support.db")
engine = create_async_engine(DATABASE_URL)
Session = async_sessionmaker(engine, expire_on_commit=False)

VALID_STATUSES = {"OPEN", "IN_REVIEW", "RESOLVED"}


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"
    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    order_id: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String, unique=True)
    chunk_count: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---------- messages ----------
async def save_message(session_id: str, role: str, content: str):
    async with Session() as s:
        if not await s.get(Conversation, session_id):
            s.add(Conversation(session_id=session_id))
        s.add(Message(session_id=session_id, role=role, content=content))
        await s.commit()


async def load_messages(session_id: str) -> list[Message]:
    async with Session() as s:
        res = await s.execute(
            select(Message).where(Message.session_id == session_id).order_by(Message.id)
        )
        return list(res.scalars().all())


# ---------- tickets ----------
async def insert_ticket(session_id: str, order_id: str, description: str) -> Ticket:
    async with Session() as s:
        t = Ticket(session_id=session_id, order_id=order_id,
                   description=description, status="OPEN")
        s.add(t)
        await s.commit()
        await s.refresh(t)
        return t


async def fetch_ticket(ticket_id: int) -> Ticket | None:
    async with Session() as s:
        return await s.get(Ticket, ticket_id)


async def set_ticket_status(ticket_id: int, status: str) -> Ticket | None:
    async with Session() as s:
        t = await s.get(Ticket, ticket_id)
        if not t:
            return None
        t.status = status
        await s.commit()
        await s.refresh(t)
        return t


# ---------- documents ----------
async def upsert_document(filename: str, chunk_count: int):
    async with Session() as s:
        await s.execute(delete(Document).where(Document.filename == filename))
        s.add(Document(filename=filename, chunk_count=chunk_count))
        await s.commit()


async def list_documents_db() -> list[Document]:
    async with Session() as s:
        res = await s.execute(select(Document).order_by(Document.id))
        return list(res.scalars().all())
