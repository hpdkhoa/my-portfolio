# Engineering Portfolio — Systems, Applied LLMs, and GPU Optimization

> A showcase of production systems I've designed and built, presented as **architecture and
> measured results rather than full source**. The implementations for HieuLuat and gen-system
> are proprietary; what's here is the engineering thinking, the design decisions, the
> benchmarks, and selected non-sensitive snippets — enough to evaluate the work and to discuss
> any of it in depth.

---

## About me

I'm Khoa. I spent a year at National Australia Bank and two and a half years at FPT Software as a solution architect, migrating legacy systems to cloud-native architectures. The recurring problem was never the target design — it was that nobody could say for certain what the old system actually did.

Since November 2025 I've been building my own systems full time: a Go engine that reads legacy code and generates verified replacements, and a Vietnamese legal RAG system that refuses to answer without citing the law. Both follow one principle — **measure it, don't assume it.**

---

## Why this repo is structured the way it is

This is a deliberate **closed-source showcase**, which is standard practice for production work with IP, proprietary data, or domain sensitivity. Each project here is real and shipped; the code that runs it stays private. What I publish instead is what actually demonstrates engineering ability: **how the system is built, why I made the calls I made, and what the numbers say.** Every claim in these writeups is something I can walk through, derive, and defend in a technical conversation.

If you're a hiring manager or interviewer: the writeups are the fastest way to assess scope and judgment. I'm happy to do a deep technical dive on architecture, trade-offs, or benchmarks for any project, and to share additional detail under NDA where appropriate.

## What's inside

| Project | One line | Stack | Where |
|---|---|---|---|
| **HieuLuat** | A Vietnamese-first legal RAG system with grounding guarantees and safety-by-construction | Python · pgvector · GPU embeddings (bge-m3) · cross-encoder rerank | [`projects/hieuluat/`](projects/hieuluat/) |
| **gen-system** | A local-first code-intelligence + code-generation engine with a benchmark harness and regression gating | Go · local LLMs via Ollama · compiler-accurate analysis | [`projects/gen-system/`](projects/gen-system/) |
| **Beastwarden** | A deterministic tactics roguelite: pure seeded core, guard-enforced invariants, ~2k tests — and a case study in directing AI-assisted development | TypeScript · Vite · Pixi · Vitest | [`projects/beastwarden/`](projects/beastwarden/) |
| **GPU / inference optimization** | Opening the "black box": indexing, reranking, quantization, batching, KV-cache, roofline | Python · CUDA concepts · Nsight methodology | [`writeups/`](writeups/) |

## The writeups

- [`writeups/01-hieuluat-retrieval-optimization.md`](writeups/01-hieuluat-retrieval-optimization.md) — making a legal RAG retrieval path fast and trustworthy: vector indexing, two-stage retrieve-then-rerank, FP16 embeddings, and the recall-vs-latency-vs-quality trade-offs measured on real eval suites.
- [`writeups/02-gen-system-inference-optimization.md`](writeups/02-gen-system-inference-optimization.md) — tuning local-LLM inference for a code engine: GPU-layer offload, streaming, quantization-as-a-measured-variable, and two-model VRAM contention — adjudicated by an *objective* quality metric (does generated code compile and pass tests).
- [`writeups/03-reproducible-benchmarking.md`](writeups/03-reproducible-benchmarking.md) — the methodology that ties it together: frozen baselines, regression gates, and deterministic runs, applied across both projects.

## Selected snippets

The [`snippets/`](snippets/) folder contains small, **self-contained, non-proprietary** illustrations of techniques used in these systems — written to run on their own with toy data, so the *idea* is legible without exposing the production code. See [`snippets/README.md`](snippets/README.md).

## What I'm optimizing for next

Converting the GPU work from *understanding* to *demonstrated kernels* — a hand-written, profiled CUDA kernel against one of these systems' hot paths, with before/after Nsight traces and a roofline analysis. (Tracked in the writeups as "future work.")

## Contact & licensing

**Dang Khoa Hoang Pham** · [hpdkhoa2311@gmail.com](mailto:hpdkhoa2311@gmail.com) · [github.com/hpdkhoa](https://github.com/hpdkhoa)

The **writeups, architecture docs, and snippets in this repo** are shared for portfolio review (see [`LICENSE`](LICENSE)). The **underlying HieuLuat and gen-system implementations are proprietary and not included.** For a deeper walkthrough, reach out — details available on request, and under NDA where the material is sensitive.
