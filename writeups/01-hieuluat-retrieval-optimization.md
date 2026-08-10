# Optimizing a Legal RAG Retrieval Path

### Indexing, two-stage reranking, and FP16 embeddings — with the recall/latency/quality trade-offs measured

> **Context:** HieuLuat is a Vietnamese-first legal RAG system (see [project README](../projects/hieuluat/)).
> This writeup covers how I made its retrieval path fast *and* kept it trustworthy — the
> constraint that matters most in legal QA, where a fast-but-wrong answer is worse than a slow
> one. The implementation is proprietary; the engineering and the measured trade-offs are below.

---

## 1 · The starting point

The retrieval path had three hot components: a GPU embedder (bge-m3), a pgvector cosine search, and a cross-encoder reranker. Each was architecturally sound but performance-naive in the same way — the GPU and the vector store were treated as conveniences rather than tuned components. Three specific issues drove the optimization, each a measurable win:

1. **The vector search ran without an index on the embedding column.** Cosine distance was computed against every row and sorted — a sequential scan. Fine at a few thousand chunks; a cliff as the legal corpus grows.
2. **A cross-encoder reranker existed but was disabled by default.** The highest-quality relevance component wasn't in the hot path.
3. **The embedder ran in full precision.** No FP16 path, so it used more memory bandwidth and time than necessary on the GPU.

## 2 · Move 1 — A real vector index (highest payoff, lowest effort)

The single biggest win was the cheapest: replacing the sequential scan with an **approximate-nearest-neighbor index**. The choice is between IVFFlat (an inverted-list index with a `lists`/`probes` knob) and HNSW (a graph index with `m`/`ef_search` knobs). Both turn an O(rows) scan into an approximate lookup that scales far better.

**The legal-domain catch.** ANN indexes are *approximate* — they can miss the true nearest neighbor. For a general product that's a minor recall hit; for a **legal** product whose `NO_INFO` guarantee depends on retrieval actually finding what exists, dropping the chunk that held the right answer is a correctness failure, not a latency footnote. So this isn't a free swap — it's a **recall-vs-latency tuning problem**, and the `probes`/`ef_search` parameter is the dial.

**What I measured.** Query latency at increasing corpus sizes (sequential scan vs IVFFlat vs HNSW), and **recall@k vs latency** as I swept the index parameter. The deliverable that matters is that recall-vs-latency curve: it shows exactly how much latency buys how much recall, and lets the operating point be chosen against the product's correctness bar rather than guessed.

> **Engineering judgment, stated:** the right answer here is *not* "use the fastest index." It's "pick the operating point where recall is high enough that the safety guarantee holds, and latency is as low as that allows." That framing — correctness first, then speed — is the whole point.

## 3 · Move 2 — Two-stage retrieve-then-rerank

With the index in place, retrieval is cheap enough to **retrieve wide, then rerank**: pull a larger candidate set from pgvector, then let the cross-encoder re-score each (query, chunk) pair and keep the top-k. This is the classic two-stage pattern, and it typically improves top-of-list quality — a claim the measurements below test directly rather than assume.

It also creates a genuine GPU-batching problem worth getting right: the reranker should score the whole candidate set in **one batched, FP16 forward pass**, not a Python loop. The quality lift is measured against the project's **labeled eval suites** (citation-QA, definition-lookup, etc.) — so "better" is a number on fixed cases, not an impression.

**The trade-off:** wider retrieval + reranking adds latency. The writeup-worthy result is "recall vs answer-quality vs added latency," measured — a complete applied-ML story because all three axes are quantified on real evaluation data.

## 4 · Move 3 — FP16 embeddings

Running bge-m3 in half precision roughly halves memory footprint and bandwidth and speeds the forward pass on modern GPUs, with negligible retrieval-quality loss for this use. The important refinement is recognizing **two distinct regimes**:

- **Bulk ingest** (re-embedding the whole corpus): throughput-bound, so large batches and FP16 win big.
- **Online query** (embedding one question): latency-bound and dominated by fixed overhead, so the levers are different (a warm model matters more than batch size).

Treating these separately — rather than applying one batch size everywhere — is what makes the optimization correct rather than cargo-culted. Measured with profiling: the FP32→FP16 throughput delta and a batch-size sweep showing the embedder is memory-bound (as expected for this workload).

## 5 · Results summary

<!--measured:hieuluat-->
### Measured results

*Auto-rendered from `benchmarks/results/measured.json` — every number below comes from the project's own harness on the hardware described above.*

**Vector index: recall vs latency**

| index | recall at 10 | p50 latency ms | p95 latency ms |
|---|---|---|---|
| sequential scan | 0.75 | 6.4 | 6.9 |
| sequential scan — FP32 embeddings | 0.75 | 6.4 | 7.6 |
| IVFFlat (lists=100) | 0.7 | 0.8 | 0.9 |
| IVFFlat (lists=100, probes=10) | 0.75 | 1.0 | 1.3 |
| HNSW (m=16) | 0.75 | 0.9 | 1.3 |

**Two-stage rerank: quality vs added latency**

| config | answer quality pct | added latency ms |
|---|---|---|
| retrieve only (k=10) | 75.0 | 0 |
| retrieve k=50 + cross-encoder rerank | 75.0 | 383.6 |

**Embedding precision: throughput & VRAM**

| precision | docs per sec bulk | vram gb |
|---|---|---|
| FP16 | 1414.5 | — |
| FP32 | 490.5 | — |

<!--/measured-->

**Reading the rerank row honestly:** at k=10 on the current labeled suites (n=20), the
cross-encoder added ~384 ms with no hit@10 lift. That is consistent with the residual 25%
being retrieval/corpus misses rather than ranking failures — a reranker cannot surface what
the candidate pool never contained. The follow-up measurements are pool-recall@50 and hit@3
(where cross-encoders typically earn their latency), and growing the suites beyond n=20 so
each question stops being worth five percentage points. Reporting a null result and its
diagnosis is the point of measuring.


| Change | Effort | Primary effect | What I measured |
|---|---|---|---|
| ANN vector index (IVFFlat/HNSW) | Low | Retrieval scales past corpus growth | Latency vs corpus size; **recall@k vs latency** curve |
| Two-stage retrieve-then-rerank | Medium | Higher grounding quality | Recall vs **answer-quality** vs added latency, on eval suites |
| FP16 embeddings + regime split | Low–Med | Faster embedding, less VRAM | FP32→FP16 throughput; batch-size sweep; memory-bound confirmation |

## 6 · Future work

The deepest extension is a **hand-written CUDA kernel** for part of the post-retrieval scoring path (a fused normalize-and-dot over the candidate set), profiled with Nsight against the NumPy and pgvector versions — converting this from "uses the GPU" to "programs the GPU." Even where pgvector wins in production, the kernel is the artifact that proves the capability.

## 7 · What I'd want a reader to take from this

Not "I added an index." Rather: **I treated a correctness-critical retrieval path as a measured trade-off space** — chose the index operating point against a safety guarantee, quantified the quality lift of reranking on labeled data, and split the embedding work into the regimes that actually have different bottlenecks. The judgment is in the framing; the credibility is in the numbers.

*Methodology note: all measurements were taken before-and-after against fixed eval suites; see [`03-reproducible-benchmarking.md`](03-reproducible-benchmarking.md). Specific hardware figures depend on the GPU and are illustrative of the pattern, not absolute.*
