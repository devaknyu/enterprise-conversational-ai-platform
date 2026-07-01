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

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main() -> None:
    """Ingest all knowledge base documents into ChromaDB."""
    ...


if __name__ == "__main__":
    main()
