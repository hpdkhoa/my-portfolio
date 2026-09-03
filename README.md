# Engineering Portfolio: Systems, Applied LLMs, and GPU Work

> Production systems I have designed and built, presented as architecture and measured results.
> gen-system is open source under Apache-2.0. HieuLuat is proprietary, so for it the writeup and
> the measured tables stand in for the code. Every measured number in this repo links to the
> harness run and the commit that produced it, so the claims can be checked without me in the room.

---

## About me

I am Khoa. I spent a year at National Australia Bank and two and a half years at FPT Software as a
solution architect, moving legacy systems to cloud native architectures.

The hard part was never the target design. It was that nobody could say for certain what the old
system actually did. That is a black box problem. An AI model has the same problem with your code,
and you usually find out when the output is wrong.

Since November 2025 I have been building my own systems full time. One is a Go engine that makes
an AI model's beliefs about a codebase visible and checkable. It grounds the model in a
deterministic graph built from the AST, and it verifies the output from outside. Its proving
ground is legacy code, COBOL and CA Gen included. The other is a Vietnamese legal question
answering system that refuses to answer without citing the law. Both follow one rule: **measure
it, do not assume it.**

---

## Why this repo looks like this

Each project here is real and shipped. One of them, gen-system, is open source. The code, the
tests, the benchmark drivers, and the engineering docs are all public. The other two stay private.
HieuLuat holds real legal data. Beastwarden is still in development.

For the private ones, what is published is the part that shows the engineering: how the system is
built, why I made the calls I made, and what the numbers say. Every claim points at the code, the
test, or the measured run behind it.

If you are hiring, start with the writeups. Each one includes a section on something that went
wrong and what it cost, because that is where judgment shows. Writeup 03 states exactly how every
number was produced, and gen-system's task set is committed before the first run, so it cannot be
tuned to the results.

## The projects

| Project | What it is | Stack | Where |
|---|---|---|---|
| **HieuLuat** | A Vietnamese legal question answering system that will not answer without grounding | Python, pgvector, GPU embeddings (bge-m3), cross encoder rerank | [projects/hieuluat/](projects/hieuluat/) |
| **gen-system** | Makes an AI model's beliefs about code visible and checkable, grounds it in a graph built from the AST, and verifies the output from outside | Go, local LLMs via Ollama, deterministic graph RAG | [projects/gen-system/](projects/gen-system/) |
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
[LICENSE](LICENSE). gen-system is published separately under Apache-2.0. The HieuLuat
implementation is proprietary and not included here.
