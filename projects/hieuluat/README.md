# HieuLuat — Vietnamese-First Legal RAG

> A retrieval-augmented question-answering system for Vietnamese law, built around **grounding
> guarantees and safety-by-construction**: it answers only from retrieved statute, cites its
> sources, and refuses when the corpus doesn't contain an answer. **Source is proprietary; this
> is the architecture and the engineering rationale.**

---

## Fast facts

- **Pipeline:** 7 idempotent stages — scrape → extract → chunk → embed → retrieve → rerank → answer
- **Corpus:** <!--stat:hl_documents-->11<!--/stat--> legal documents, <!--stat:hl_chunks-->1,583<!--/stat--> provision-aligned chunks
- **Stack:** Python (<!--stat:hl_py_loc-->52,783<!--/stat--> lines) · PostgreSQL + pgvector · bge-m3 GPU embeddings · cross-encoder rerank
- **Guarantee:** answers only from retrieved statute, with citations; structural no-information path when the corpus is silent
- **Quality gate:** labeled eval suites (citation-QA, definition-lookup) adjudicate every optimization

## The problem

Legal QA has a failure mode that ordinary RAG tolerates and law cannot: a confident answer that isn't actually grounded in the statute. The bar here is not "sounds right" — it's "every claim traces to a real legal provision, and when the corpus is silent, the system says so." HieuLuat is designed around that constraint rather than bolting it on afterward.

## Architecture (pipeline)

The system is a staged pipeline, each stage idempotent and independently testable:

1. **Scrape** — collect legal documents from authoritative sources, tracking provenance and residency per document.
2. **Extract** — separate **born-digital** text from **scanned/OCR** content and handle each appropriately, because extraction quality drives everything downstream.
3. **Chunk** — split on **article/provision boundaries** rather than fixed token windows, so each chunk is a coherent legal unit that can be cited.
4. **Embed** — encode chunks with a multilingual embedding model (bge-m3) on GPU into a vector store (pgvector), tagged by embedding-model family and source residency.
5. **Retrieve** — cosine nearest-neighbor search over the vector store, filtered by residency and model family for correctness.
6. **Rerank** — a cross-encoder re-scores the retrieved candidates for relevance (a two-stage retrieve-wide-then-rerank design).
7. **Answer** — generate a grounded answer constrained to the retrieved context, with citations and an explicit **"no information found"** path when retrieval comes up empty.

## Design decisions worth defending

- **Article-boundary chunking over fixed windows.** A legal answer must cite a provision; chunks that straddle or split provisions produce uncitable or misleading context. The chunker respects legal structure.
- **Safety-by-construction, not post-hoc filtering.** The grounding and the `NO_INFO` path are structural properties of the answer stage, not a filter applied after generation. The system is built so that an ungrounded answer is hard to produce by design.
- **Residency- and model-tagged vectors.** Because the store can hold multiple embedding-model families and documents with different residency, retrieval filters on both — these filters are load-bearing for *correctness*, not just performance.
- **Evaluation as a first-class artifact.** The project ships labeled eval suites (citation-QA, definition-lookup, and others) so that quality is measured against fixed cases, not judged by vibes. Optimizations are accepted or rejected against these suites.

## Results & optimization

The retrieval path's performance and quality work — vector indexing (sequential-scan → IVFFlat/HNSW), turning on the two-stage reranker, and FP16 embeddings — is written up in detail, including the **recall-vs-latency-vs-quality** trade-offs measured on the eval suites:

→ [`../../writeups/01-hieuluat-retrieval-optimization.md`](../../writeups/01-hieuluat-retrieval-optimization.md)

## Stack

Python · PostgreSQL + pgvector · bge-m3 embeddings (GPU) · cross-encoder reranker (bge-reranker-v2-m3) · staged, idempotent pipeline · labeled evaluation suites.

## What's not here (and why)

The implementation, the legal corpus, prompts, configuration, and any secrets are **excluded by design** — this is a legal product with data and IP considerations. The architecture above and the linked writeup are sufficient to evaluate the engineering; deeper detail is available under NDA.
