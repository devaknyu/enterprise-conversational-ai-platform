# ADR-002: Use ChromaDB as the Vector Store for RAG

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06-30 |
| **Deciders** | Platform Architecture |

---

## Context

The platform needs a Retrieval-Augmented Generation (RAG) pipeline to answer IT policy questions. When an employee asks "What are the password complexity requirements?", the system must:
1. Convert the question to a vector embedding
2. Search a pre-indexed knowledge base for the most relevant document chunks
3. Pass those chunks as context to Gemini for grounded answer generation

This requires a **vector store**: a system that stores embedding vectors alongside their source text and metadata, and supports efficient approximate nearest-neighbor search.

The knowledge base consists of:
- ~10 IT policy and procedure documents (password policy, VPN guide, software installation policy, IT support FAQ, etc.)
- ~500–2000 chunks after splitting (each chunk ~256–512 tokens)
- Metadata per chunk: `document_name`, `category`, `last_updated`, `chunk_index`

Options evaluated: **ChromaDB**, **FAISS**, **Pinecone**, **Weaviate**.

---

## Decision

**Use ChromaDB in embedded mode** with local filesystem persistence (`./knowledge_base/chroma_db/`).

ChromaDB runs in-process alongside the FastAPI application. No separate server is required. The collection is populated once by `scripts/ingest_knowledge_base.py` and queried at runtime by `RAGService`.

---

## Rationale

### 1. Persistent storage out of the box

ChromaDB persists its index and vector data to the local filesystem automatically. Restart the application — the collection is still there.

FAISS is an **in-memory library**, not a database. It provides no persistence mechanism. To persist a FAISS index, the application must manually call `faiss.write_index(index, path)` on every mutation and `faiss.read_index(path)` on startup. Source metadata (the actual document text, chunk indices, document names) must be stored separately in a parallel data structure (a dict, a SQLite file) that the application maintains in sync with the FAISS index. This is significant custom work that ChromaDB handles natively.

### 2. Metadata filtering without additional infrastructure

ChromaDB supports filtering retrieval results by metadata fields using a MongoDB-style query language:

```python
collection.query(
    query_embeddings=[embedding],
    n_results=5,
    where={"category": "password-policy"},
)
```

This enables targeted retrieval: if Dialogflow's intent is specifically `it.policy.password`, we can restrict ChromaDB to only search password-related chunks rather than the entire knowledge base — improving precision.

FAISS has no concept of metadata. It stores float32 vectors and integer IDs. Metadata association and filtering must be implemented entirely by the application layer, requiring a parallel lookup table keyed on FAISS vector ID.

### 3. Python-native API, no server process

ChromaDB's embedded mode (`chromadb.PersistentClient(path=...)`) runs entirely in-process. There is no network call, no Docker container to manage, no port to expose. The DI container initializes `RAGService` with a ChromaDB client at startup; the client is ready immediately.

For local development, this means:
```bash
# No additional services needed:
uvicorn app.main:app --reload
```

Pinecone requires an active internet connection and a managed cloud account. Weaviate requires a running Docker container or managed cloud instance. Both add infrastructure to the local development loop.

### 4. Appropriate for the knowledge base scale

The IT knowledge base is bounded: 10–50 documents, 500–2000 chunks. ChromaDB uses HNSW (Hierarchical Navigable Small World) indexing, which is well-suited to this scale and provides sub-millisecond query times for collections of this size.

The choice of vector store is not performance-critical at this scale. The embedding generation (calling Vertex AI `text-embedding-004` at query time) is the dominant latency contributor, not the ChromaDB lookup.

### 5. Zero cost in development and test environments

ChromaDB is open-source (Apache 2.0 license) and runs locally with no account, no API key, and no network dependency. The test suite can use an isolated `chroma_test_db/` directory that is created and destroyed per test session.

---

## Alternatives Considered

### FAISS (Facebook AI Similarity Search)

**Why it was considered:** FAISS is the gold-standard for high-performance approximate nearest-neighbor search. At billions of vectors, it outperforms everything else on raw speed. It is widely used in production ML systems.

**Why it was not chosen:**
- **Library, not database**: FAISS stores float32 vectors only. It has no concept of documents, metadata, or text. Every piece of application context (the actual chunk text, the document it came from, when it was ingested) must be managed in a parallel data structure that the application keeps in sync.
- **No persistence**: manual `faiss.write_index()` / `faiss.read_index()` calls required. Not a drop-in replacement for a database.
- **No metadata filtering**: filtering results by document category requires post-processing the FAISS results in application code.
- **Overkill at this scale**: FAISS's advantages (GPU support, billion-vector IVF indexes) are not relevant for a 2000-chunk knowledge base.
- **Verdict**: correct choice if the knowledge base scales to millions of vectors and raw throughput is the constraint. Document this migration path (see "When to revisit" below).

### Pinecone

**Why it was considered:** Pinecone is a fully managed vector database with a clean Python SDK, metadata filtering, and production SLAs.

**Why it was not chosen:**
- **Cost**: Pinecone charges per index and per query volume. For a development platform, this adds a cost dependency where zero cost is achievable.
- **Internet dependency in development**: Pinecone is a cloud service. Local development and CI/CD require internet access and an active Pinecone account. Test runs hit a real external API unless mocked.
- **Additional vendor**: the platform is already GCP-committed (Dialogflow CX, Vertex AI, Cloud Run). Adding Pinecone introduces a second cloud vendor for a component that can be solved locally.
- **Verdict**: the right choice if the knowledge base scales beyond what ChromaDB handles, or if multi-region replication of the vector index is required.

### Weaviate

**Why it was considered:** Weaviate is an open-source vector database with rich query capabilities, a GraphQL API, multi-tenancy, and built-in embedding models.

**Why it was not chosen:**
- **Operational complexity**: Weaviate requires a running server process (Docker container or managed cloud). This adds infrastructure to every development environment and the Cloud Run deployment.
- **Feature excess**: Weaviate's multi-tenancy, cross-references, and GraphQL API are features we do not need. Using a simpler tool for a simpler problem is correct.
- **Verdict**: appropriate if the platform evolves into a multi-tenant SaaS product where each customer has an isolated knowledge base.

---

## When to Revisit This Decision

| Trigger | Migration Path |
|---|---|
| Knowledge base > 100K chunks | FAISS with a custom metadata SQLite layer, or Pinecone |
| Multi-tenant knowledge bases (different knowledge base per department/customer) | Weaviate (built-in multi-tenancy) or Pinecone (per-tenant namespaces) |
| Distributed deployment (multiple Cloud Run regions reading the same knowledge base) | Pinecone or Vertex AI Vector Search (GCP-native, managed) |
| Sub-millisecond p99 retrieval required at high QPS | FAISS with GPU index, or Vertex AI Vector Search |

---

## Consequences

**Positive:**
- No additional infrastructure to run locally or in CI
- Persistence, metadata, and text storage handled by ChromaDB natively
- Metadata filtering available without custom code
- Open-source, no cost, no external dependency

**Negative / Trade-offs:**
- `chroma_db/` directory must be excluded from version control (gitignored)
- Knowledge base must be seeded via `scripts/ingest_knowledge_base.py` before RAG queries work; a fresh deployment has no data
- ChromaDB embedded mode does not support concurrent writes from multiple processes — acceptable since ingestion is a one-time batch operation, not a live write path
- Not suitable if the knowledge base needs to be updated in real-time (e.g., ingesting new tickets as they're resolved)

**Operational requirements:**
- `CHROMA_PERSIST_DIR` must point to a writable directory with sufficient disk space
- In Cloud Run, the persist directory must be on a mounted volume (Cloud Run filesystem is ephemeral) — or ingestion must run on startup (Phase 8/9 consideration)
