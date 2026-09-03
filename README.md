# Engineering Portfolio: Systems, Applied LLMs, and GPU Work

> A showcase of production systems I have designed and built. It presents architecture and
> measured results rather than full source. The code for HieuLuat and gen-system is proprietary.
> What is here is the engineering thinking, the design decisions, the benchmarks, and a few small
> snippets. That is enough to judge the work, and I can go deeper on any of it in conversation.

---

## About me

I am Khoa. I spent a year at National Australia Bank and two and a half years at FPT Software as a
solution architect, moving legacy systems to cloud native architectures.

The hard part was never the target design. It was that nobody could say for certain what the old
system actually did.

Since November 2025 I have been building my own systems full time. One is a Go engine that reads
legacy code and generates verified replacements. The other is a Vietnamese legal question answering
system that refuses to answer without citing the law. Both follow one rule: **measure it, do not
assume it.**

---

## Why this repo looks like this

This is a closed source showcase, which is normal for production work with IP or sensitive data.
Each project here is real and shipped. The code that runs it stays private.

What I publish instead is the part that shows engineering ability: how the system is built, why I
made the calls I made, and what the numbers say. Every claim in these writeups is something I can
walk through and defend.

If you are hiring: the writeups are the fastest way to judge scope and judgment. I am happy to go
deep on architecture, trade offs, or benchmarks, and to share more under NDA where that fits.

## The projects

| Project | What it is | Stack | Where |
|---|---|---|---|
| **HieuLuat** | A Vietnamese legal question answering system that will not answer without grounding | Python, pgvector, GPU embeddings (bge-m3), cross encoder rerank | [projects/hieuluat/](projects/hieuluat/) |
| **gen-system** | A local code understanding and generation engine with its own benchmark harness | Go, local LLMs via Ollama, compiler accurate analysis | [projects/gen-system/](projects/gen-system/) |
| **Beastwarden** | A deterministic tactics roguelite with a seeded core and about 2,000 tests. Also a case study in directing AI assisted development | TypeScript, Vite, Pixi, Vitest | [projects/beastwarden/](projects/beastwarden/) |
| **GPU and inference work** | Indexing, reranking, quantization, batching, KV cache, roofline | Python, CUDA concepts, Nsight method | [writeups/](writeups/) |

## The writeups

Start here. They are the point of the repo.

- **[Making a legal search path fast and still correct](writeups/01-hieuluat-retrieval-optimization.md)**
  Vector indexing, retrieve then rerank, FP16 embeddings. Includes a negative result: the reranker
  cost 384 ms and improved nothing, and section 6 works out which component that actually blames.

- **[Tuning local LLM inference for a code engine](writeups/02-gen-system-inference-optimization.md)**
  GPU offload, streaming, quantization as a measured variable, and two models sharing one 16 GB
  card. Section 4 is about discovering my own quality metric was broken, and what replaced it.

- **[Reproducible benchmarking and regression gates](writeups/03-reproducible-benchmarking.md)**
  The method underneath both: frozen baselines, gates, repeatable runs, and why an objective
  metric that cannot move is worse than a proxy.

## Snippets

The [snippets/](snippets/) folder has small Python files that run on their own with toy data. They
show the ideas from the writeups without any production code in them.

## What I am working on next

Turning the GPU work from understanding into a demonstrated kernel: a hand written, profiled CUDA
kernel against one of these systems, with Nsight traces before and after and a roofline analysis.
This is tracked as future work in
[writeup 01](writeups/01-hieuluat-retrieval-optimization.md), which also states the honest limit up
front. The scoring path it targets is under 1 ms of a 385 ms request, so the kernel is a capability
demonstration, not an end to end speedup.

## Contact and licensing

**Dang Khoa Hoang Pham**
[hpdkhoa2311@gmail.com](mailto:hpdkhoa2311@gmail.com) · [github.com/hpdkhoa](https://github.com/hpdkhoa)

The writeups, architecture docs, and snippets in this repo are shared for portfolio review. See
[LICENSE](LICENSE). The HieuLuat and gen-system implementations are proprietary and not included
here. For a deeper walkthrough, get in touch. More detail is available on request, and under NDA
where the material is sensitive.
