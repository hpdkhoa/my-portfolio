# Making a Legal Search Path Fast and Still Correct

### Vector indexing, reranking, and FP16 embeddings, with the trade offs measured

> **Context:** HieuLuat is a Vietnamese legal question answering system (see
> [project README](../projects/hieuluat/)). This writeup covers how I made its search path fast
> without making it less trustworthy. In legal work, a fast wrong answer is worse than a slow
> right one. The code is proprietary. The engineering and the measurements are below.

---

## 1. Where it started

The search path had three parts that used the GPU or the database heavily: an embedder (bge-m3),
a pgvector cosine search, and a cross encoder reranker.

All three worked. None of them were tuned. Three problems stood out:

1. **The vector search had no index.** Postgres computed the distance to every row, then sorted.
   That is fine for a few thousand chunks. It gets slow as the corpus grows.
2. **The reranker was switched off.** The component that judges relevance best was not being used.
3. **The embedder ran in full precision.** No FP16 path, so it used more memory bandwidth than it
   needed to.

## 2. Move 1: add a real vector index

This was the cheapest change and the biggest win. I replaced the full scan with an approximate
nearest neighbor index. There are two options in pgvector: IVFFlat, which groups vectors into
lists, and HNSW, which builds a graph. Both replace a full scan with a lookup that scales.

**The catch is the word approximate.** These indexes can miss the true nearest neighbor. In most
products that is a small quality loss. In a legal product it is not. HieuLuat promises to say
"no information" when it cannot find an answer. If the index drops the chunk that held the answer,
the system says "no information" when the answer existed. That is a correctness bug, not a speed
tuning detail.

So this is not a free swap. It is a trade off between recall and latency, and the `probes` or
`ef_search` setting is the dial.

**What I measured.** Query latency as the corpus grows, for full scan, IVFFlat, and HNSW. Then
recall at k against latency as I turned the dial. That second curve is the useful one. It shows
how much latency buys how much recall, so the operating point can be chosen against the
correctness bar instead of guessed.

The goal was never to use the fastest index. It was to find the point where recall stays high
enough to keep the promise. Then take the lowest latency available at that point.

## 3. Move 2: retrieve wide, then rerank

Once the index was in place, retrieval became cheap enough to pull a larger candidate set and
rescore it. The cross encoder scores each question and chunk pair, then keeps the best few.

This is a standard two stage pattern. It usually improves how well answers are grounded in the
source, which for legal work is the metric that matters.

It also creates a GPU batching problem worth solving properly. The reranker should score the whole
candidate set in one batched FP16 forward pass, not in a Python loop.

The cost is latency. Retrieving more and reranking it takes time. So the result to report has three
axes: recall, answer quality, and the added milliseconds.

## 4. Move 3: FP16 embeddings

Running bge-m3 in half precision roughly halves the memory it needs and the bandwidth it uses. On
a modern GPU it also speeds up the forward pass. Quality loss for this use is negligible.

The part worth getting right is that there are two different jobs here, and they have different
bottlenecks:

- **Bulk ingest**, when embedding again the whole corpus, is limited by throughput. Large batches and
  FP16 help a lot.
- **Online query**, when embedding one question, is limited by latency and fixed overhead. Batch
  size barely matters. Keeping the model warm matters more.

Using one batch size for both jobs is the common mistake. I measured them separately: the FP32 to
FP16 throughput difference, and a batch size sweep showing the embedder is limited by memory
bandwidth, which is what you would expect.

## 5. Results

<!--measured:hieuluat-->
<!--/measured-->

| Change | Effort | Effect | What I measured |
|---|---|---|---|
| Vector index (IVFFlat or HNSW) | Low | Search scales as the corpus grows | Latency against corpus size, recall at k against latency |
| Retrieve wide, then rerank | Medium | Better grounded answers | Recall, answer quality, added latency |
| FP16 embeddings | Low | Faster embedding, less VRAM | FP32 to FP16 throughput, batch size sweep |

## 6. The recall ceiling, and why reranking did not help

One result in that table looks like a failure. It is worth reading carefully, because the
interesting part is which component it actually blames.

Recall at 10 is 0.75 on the full scan. **The full scan is exhaustive.** It compares the question to
every row, so there is no approximation in it to lose recall to. That means 0.75 is not a result
about the index at all. It is the ceiling of what this embedding model finds at k equals 10 on this
evaluation set. About a quarter of the correct chunks are not in the top ten under any index.

Read against that ceiling, the index work did exactly what it should. HNSW and tuned IVFFlat both
return 0.75, matching the exhaustive scan, while cutting median latency from 6.4 ms to about 1 ms.
Untuned IVFFlat sits at 0.70, which is the honest cost of leaving `probes` at its default and the
reason the tuning step was not optional. So the index bought a roughly six times latency
reduction at no cost to recall. It did not "stay flat."

**The reranker is a different story, and a genuinely negative result.** Retrieving 50 candidates
and rescoring them added 384 ms and changed answer quality by nothing.

That follows from the ceiling above. A reranker reorders the candidates it is given. It cannot find
a chunk that retrieval never returned. If the right chunk is missing from the candidate set, no
amount of rescoring brings it back.

**What I have not separated yet.** A flat 0.75 across every configuration is also what a broken
evaluation set looks like. The measurement that tells the two apart is recall at 50, which is the
candidate set the reranker actually sees.

- If recall at 50 is also around 0.75, the misses are real retrieval misses. Then the fix is
  upstream of both the index and the reranker: better chunking, hybrid keyword and vector search,
  or a better embedding model for Vietnamese legal text.
- If recall at 50 is much higher, the candidates were there and the reranker failed to promote
  them. That is a reranker problem, and an easier one.

Until that number exists, the honest claim is the narrow one. The index is not the bottleneck, and
the reranker is not paying for its 384 ms.

**Status of the reranker:** `[TODO: keep or drop, Khoa's call.]` If it was dropped, say so plainly.
Removing a component that costs 384 ms and buys nothing measurable is good engineering.

## 7. Future work

The deepest extension is a hand written CUDA kernel for part of the scoring path. It would fuse the
normalize and dot product steps over the candidate set. I would profile it with Nsight against the
NumPy and pgvector versions. That moves this from using the GPU to programming the GPU.

One caveat I should state rather than let a reader work out. The scoring path is under 1 ms of a
request that currently takes about 385 ms. So a kernel there is a capability demonstration, not an
end to end speedup. The honest version of this work says that up front, shows the roofline that
predicts the result, and then measures it.

## 8. What I would want a reader to take from this

Not "I added an index." Rather: I treated a correctness critical search path as a set of measured
trade offs. I chose the index operating point against a safety promise, and I split the embedding
work into the two jobs that actually have different bottlenecks.

The part I would point at first is section 6. The reranking result was negative. The recall number
looked flat enough to be embarrassing. The useful work was figuring out which component the number
actually blames, and naming the one measurement that would settle it. That is worth more than
another win would have been.

*Measurements were taken before and after against fixed evaluation sets. See
[reproducible benchmarking](03-reproducible-benchmarking.md). Hardware numbers depend on the GPU.
The pattern transfers; the absolute values do not.*
