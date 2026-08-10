# gen-system — Local-First Code Intelligence & Generation

> A code-generation engine that runs entirely locally, pairs **compiler-accurate program
> analysis** with **local LLMs**, and holds itself to an objective bar: **generated code must
> compile and pass tests**. It ships with a benchmark harness and regression gating so quality
> is measured, not assumed. **Source is proprietary; this is the architecture and rationale.**

---

## Fast facts

- **Releases shipped:** <!--stat:gen_releases-->23<!--/stat--> (solo, since 11/2025)
- **Engine:** Go — <!--stat:gen_go_files-->318<!--/stat--> source files, <!--stat:gen_go_loc-->58,933<!--/stat--> lines
- **Languages analyzed:** Go, TypeScript, Python, COBOL/CICS, CA Gen — exact symbol resolution, call graphs, CFGs
- **Inference:** role-split local models via Ollama on a single RTX 4060 Ti 16 GB — **qwen3:14b** planner + **qwen2.5-coder:14b** coder (≈9 GB each; deliberate VRAM-contention management) — with a measured quantization study (Q4/Q5/Q8) on DeepSeek-Coder-V2 16B
- **Quality gate:** 11 benchmark suites, frozen baselines, deterministic runs (temp 0, fixed seed)

## The idea

Most code-generation tooling is a thin wrapper over a remote model and trusts the output. gen-system inverts both: it runs **local-first** (no data leaves the machine), and it treats generation as something to be **verified and benchmarked** rather than trusted. The organizing principle is determinism and measurability — same input, same output, and a quality metric that can't be fudged.

## Architecture

- **Analysis layer.** Compiler-accurate symbol resolution plus call-graph and control-flow analysis, so the system reasons about real program structure rather than treating code as text.
- **Generation layer.** Local LLMs via Ollama, with **separate models for planning and for code** (a planner model and a coder model), run at temperature 0 with a fixed seed for **deterministic, reproducible** output. A deterministic-template path exists as an alternative to model generation.
- **Verification layer.** Generated projects are expected to **build and pass tests** — this is the quality signal the whole system is tuned against.
- **Benchmark harness.** Frozen baselines and **regression gates**: a change that lowers the compile/test pass rate is caught automatically, not discovered later.
- **Orchestration.** Robust runtime handling — retries, structured-output constraints, model keep-alive to avoid mid-run reloads — around the model calls.

## Design decisions worth defending

- **Local-first by default.** Privacy and reproducibility over the convenience of a hosted API. The whole pipeline runs on your hardware.
- **Determinism (temp 0, fixed seed).** Generation is reproducible, which is what makes benchmarking meaningful — you're measuring the system, not sampling noise.
- **Two specialized models over one general one.** Planning and code generation are different tasks; specializing improves quality, at the cost of a real **VRAM-contention** problem (two models on one GPU) that the system manages with keep-alive and timeout tuning.
- **An objective quality metric.** Because the bar is "does it compile and pass tests," quality regressions are visible and gateable — a meaningful advantage over perplexity-style proxies. This is rare and worth highlighting.

## Results & optimization

The inference-tuning work — GPU-layer offload, output streaming, **quantization treated as a measured variable** (not a fixed choice), and resolving two-model VRAM contention — is written up with the **tokens/sec vs VRAM vs compile-pass-rate** trade-offs:

→ [`../../writeups/02-gen-system-inference-optimization.md`](../../writeups/02-gen-system-inference-optimization.md)

The benchmarking methodology (frozen baselines, regression gates, deterministic runs) is its own writeup:

→ [`../../writeups/03-reproducible-benchmarking.md`](../../writeups/03-reproducible-benchmarking.md)

## Stack

Go · local LLMs via Ollama (planner + coder models) · compiler-accurate analysis (symbol resolution, call/control-flow graphs) · deterministic generation (temp 0, fixed seed) · benchmark harness with regression gating.

## What's not here (and why)

The implementation, prompts, templates, and configuration are **excluded by design**. The architecture above and the linked writeups are enough to evaluate the engineering and discuss it in depth; more is available on request.
