"""One-time script to ingest knowledge base documents into ChromaDB.

Reads all .md files from knowledge_base/documents/, splits them into chunks,
generates embeddings via the configured EMBEDDING_BACKEND, and stores them
in ChromaDB at CHROMA_PERSIST_DIR.

Run once before using the RAG pipeline:
    python scripts/ingest_knowledge_base.py

Re-run after adding or updating documents. The collection is cleared and
re-built from scratch to avoid stale embeddings.

Implemented in Phase 6.
"""

import asyncio
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
import structlog

from app.config import Settings
from app.services.platform.embedding_backends.local import LocalEmbeddingBackend

# Chunk size / overlap in characters. Smaller than token-based for simplicity;
# the IT policy docs are short enough that 2000 chars ≈ 300-400 tokens.
_CHUNK_SIZE = 2000
_CHUNK_OVERLAP = 200
_EMBED_BATCH_SIZE = 32

_METADATA_RE = re.compile(
    r"Document ID:\s*(\S+)\s*\|\s*Category:\s*([\w-]+)\s*\|\s*Last Updated:\s*(\S+)"
)


def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character windows, breaking on newlines where possible."""
    chunks: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        # Walk back to the nearest newline so we don't split mid-sentence.
        if end < length:
            newline_pos = text.rfind("\n", start, end)
            if newline_pos > start:
                end = newline_pos + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap if end < length else length
    return chunks


async def ingest(settings: Settings) -> None:
    """Load, chunk, embed, and store all knowledge base documents."""
    logger = structlog.get_logger("ingest")
    docs_dir = Path(__file__).parent.parent / "knowledge_base" / "documents"
    md_files = sorted(docs_dir.glob("*.md"))

    if not md_files:
        logger.error("no_documents_found", path=str(docs_dir))
        sys.exit(1)

    logger.info("ingest_start", document_count=len(md_files))

    backend = LocalEmbeddingBackend(
        model_name=settings.embedding_model_local,
        logger=logger,
    )

    all_ids: list[str] = []
    all_texts: list[str] = []
    all_metadatas: list[dict] = []

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Metadata is on the second line (index 1) of each document.
        document_id = md_file.stem
        category = md_file.stem
        last_updated = ""
        if len(lines) > 1:
            match = _METADATA_RE.search(lines[1])
            if match:
                document_id = match.group(1)
                category = match.group(2)
                last_updated = match.group(3)

        chunks = _chunk_text(content)
        logger.info(
            "document_chunked",
            file=md_file.name,
            document_id=document_id,
            category=category,
            chunk_count=len(chunks),
        )

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_{idx}"
            all_ids.append(chunk_id)
            all_texts.append(chunk)
            all_metadatas.append({
                "document_id": document_id,
                "category": category,
                "source_file": md_file.name,
                "chunk_index": idx,
                "last_updated": last_updated,
            })

    # Embed in batches.
    logger.info("embedding_start", total_chunks=len(all_texts))
    t0 = time.monotonic()
    all_vectors: list[list[float]] = []
    for batch_start in range(0, len(all_texts), _EMBED_BATCH_SIZE):
        batch = all_texts[batch_start : batch_start + _EMBED_BATCH_SIZE]
        vectors = await backend.embed(batch)
        all_vectors.extend(vectors)
        logger.info(
            "embedding_batch_complete",
            batch_end=min(batch_start + _EMBED_BATCH_SIZE, len(all_texts)),
            total=len(all_texts),
        )
    elapsed = time.monotonic() - t0
    logger.info("embedding_complete", total_chunks=len(all_vectors), elapsed_s=round(elapsed, 2))

    # Store in ChromaDB, clearing any existing collection first.
    persist_dir = settings.chroma_persist_dir
    collection_name = settings.chroma_collection_name
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=persist_dir)

    try:
        client.delete_collection(name=collection_name)
        logger.info("collection_cleared", collection=collection_name)
    except Exception:
        pass  # Collection did not exist yet — that's fine.

    collection = client.create_collection(name=collection_name)
    collection.add(
        ids=all_ids,
        documents=all_texts,
        embeddings=all_vectors,
        metadatas=all_metadatas,
    )

    logger.info(
        "ingest_complete",
        collection=collection_name,
        persist_dir=persist_dir,
        total_chunks=len(all_ids),
    )


def main() -> None:
    """Ingest all knowledge base documents into ChromaDB."""
    import logging
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )

    settings = Settings()
    asyncio.run(ingest(settings))


if __name__ == "__main__":
    main()
