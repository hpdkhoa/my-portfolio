# HieuLuat: Vietnamese legal question answering

> A system that answers questions about Vietnamese law using only retrieved statute. It cites its
> sources. When the corpus does not contain an answer, it says so instead of guessing. The source
> is proprietary. This page covers the architecture and the reasoning.

---

## Fast facts

- **Pipeline:** 7 stages, each repeatable: scrape, extract, chunk, embed, retrieve, rerank, answer
- **Corpus:** <!--stat:hl_documents--><!--/stat--> legal documents, <!--stat:hl_chunks--><!--/stat--> chunks aligned to provisions
- **Stack:** Python (<!--stat:hl_py_loc-->52,783<!--/stat--> lines), PostgreSQL with pgvector, bge-m3 GPU embeddings, cross encoder rerank
- **Promise:** every answer comes from retrieved statute and carries citations. There is a built in path for "no information found"
- **Quality gate:** labeled evaluation sets decide whether an optimization is accepted

## The problem

Legal question answering has one failure mode that ordinary systems tolerate and law cannot. That
is a confident answer which is not actually grounded in the statute.

The bar here is not that the answer sounds right. It is that every claim traces to a real legal
provision, and that the system admits it when the corpus is silent. HieuLuat is built around that
constraint rather than having it added afterwards.

## The pipeline

Seven stages. Each one can be rerun safely and tested on its own.

1. **Scrape.** Collect legal documents from official sources, tracking where each one came from.
2. **Extract.** Separate born digital text from scanned pages that need OCR, and handle each
   properly. Extraction quality decides everything downstream.
3. **Chunk.** Split on article and provision boundaries, not on fixed token counts. Each chunk is
   then a complete legal unit that can be cited.
4. **Embed.** Encode chunks with bge-m3 on the GPU into pgvector, tagged by embedding model family
   and by source.
5. **Retrieve.** Cosine nearest neighbor search, filtered by source and model family.
6. **Rerank.** A cross encoder rescores the retrieved candidates. This is the second stage of a
   retrieve wide then rerank design.
7. **Answer.** Generate an answer limited to the retrieved context, with citations, and an explicit
   "no information found" path when retrieval returns nothing useful.

## Design decisions, and why

**Chunking on article boundaries, not fixed windows.** A legal answer has to cite a provision. A
chunk that splits or straddles provisions produces context you cannot cite. So the chunker follows
legal structure.

**Grounding built in, not filtered afterwards.** The citation requirement and the no information
path are properties of the answer stage itself. They are not a filter bolted on after generation.
The system is built so that an ungrounded answer is hard to produce.

**Vectors tagged by source and model family.** The store can hold several embedding model families
and documents from different sources. Retrieval filters on both. Those filters exist for
correctness, not for speed.

**Evaluation sets as a real deliverable.** The project ships labeled evaluation sets. Quality is
measured on fixed cases rather than judged by impression. An optimization is accepted or rejected
against them.

## Results

The performance and quality work on the retrieval path is written up in detail. That covers the
vector index, turning on the reranker, and FP16 embeddings, with the trade offs measured:

→ [Making a legal search path fast and still correct](../../writeups/01-hieuluat-retrieval-optimization.md)

Worth reading section 6 of that writeup. The reranker turned out to add 384 ms and improve nothing,
and the useful work was figuring out which component that result actually blames.

## Stack

Python. PostgreSQL with pgvector. bge-m3 embeddings on GPU. A cross encoder reranker
(bge-reranker-v2-m3). A staged pipeline where every stage is repeatable. Labeled evaluation sets.

## What is not here, and why

The implementation, the legal corpus, the prompts, the configuration, and any secrets are left out
on purpose. This is a legal product with real data.

What is public is the architecture above and the retrieval writeup. Its numbers come from the
evaluation harness described in [writeup 03](../../writeups/03-reproducible-benchmarking.md), and
its section 6 reports the result that did not go the way I wanted.
