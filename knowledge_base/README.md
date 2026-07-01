# Knowledge Base

IT policy and procedure documents used by the RAG pipeline to ground Gemini responses.

## Documents

| File | Document ID | Category | Description |
|---|---|---|---|
| `password-policy.md` | IT-SEC-001 | password-policy | Password complexity, expiration, reset procedures |
| `vpn-guide.md` | IT-NET-003 | vpn-guide | VPN installation, connection, troubleshooting |
| `software-policy.md` | IT-SW-002 | software-policy | Approved software catalog, installation policy |
| `it-support-faq.md` | IT-FAQ-001 | it-support-faq | General IT FAQ — accounts, hardware, email, tickets |

## Ingestion

Run once before using the RAG pipeline. Re-run after adding or updating documents.

```bash
python scripts/ingest_knowledge_base.py
```

The script:
1. Reads all `.md` files from `knowledge_base/documents/`
2. Splits each document into 512-token chunks with 64-token overlap
3. Embeds chunks using the configured `EMBEDDING_BACKEND` (local by default — free)
4. Stores vectors and text in ChromaDB at `CHROMA_PERSIST_DIR`

ChromaDB data is gitignored. A fresh clone must re-ingest before RAG works.

## Chunking Strategy

- Chunk size: 512 tokens
- Overlap: 64 tokens
- Metadata per chunk: `document_id`, `category`, `source_file`, `chunk_index`
- The `category` field enables filtered retrieval (e.g., restrict a password query to `password-policy` chunks only)

## Adding New Documents

1. Add a `.md` file to `knowledge_base/documents/`
2. Include a frontmatter-style header at the top: `# Document ID: | Category: | Last Updated:`
3. Re-run `python scripts/ingest_knowledge_base.py`
