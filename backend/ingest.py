from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.vector_store import vstore

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)


def ingest_text(filename: str, text: str) -> int:
    chunks = splitter.split_text(text)
    ids = [f"{filename}-{i}" for i in range(len(chunks))]

    # Remove old chunks of this file so re-upload never duplicates.
    try:
        vstore.delete_by_metadata_filter({"source": filename})
    except Exception:
        # Fallback for older versions: delete by the known IDs
        vstore.delete(ids)

    vstore.add_texts(
        chunks,
        metadatas=[{"source": filename}] * len(chunks),
        ids=ids,
    )
    return len(chunks)
