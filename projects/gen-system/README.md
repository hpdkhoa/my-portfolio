# gen-system: local code understanding and generation

> A code generation engine that runs entirely on your own machine. It pairs compiler accurate
> program analysis with local LLMs, and holds the output to a real bar: the generated code has to
> build and pass its tests. It ships with a benchmark harness and regression gates, so quality is
> measured rather than assumed. The source is proprietary. This page covers the architecture and
> the reasoning.

---

## Fast facts

- **Releases shipped:** <!--stat:gen_releases-->23<!--/stat--> since November 2025, working alone
- **Engine:** Go, <!--stat:gen_go_files--><!--/stat--> source files, <!--stat:gen_go_loc--><!--/stat--> lines
- **Languages it reads:** Go, COBOL with copybooks, CA Gen, Java, TypeScript, Python. Exact symbol
  resolution, call graphs, control flow graphs
- **Inference:** open weight models through Ollama on one RTX 4060 Ti with 16 GB. `qwen3:14b` plans
  and `qwen2.5-coder:14b` writes code
- **Quality gate:** 13 benchmark suites, frozen baselines, and repeatable runs at temperature 0
  with a fixed seed.

Speed and VRAM numbers live in the [inference writeup](../../writeups/02-gen-system-inference-optimization.md),
where they are generated from measured runs. They are not repeated here, because a copied number
goes stale the first time you rerun anything.

## The idea

Most code generation tooling is a thin wrapper around a remote model, and it trusts what comes
back. This inverts both halves.

It runs locally, so no code leaves the machine. And it treats generation as something to verify and
measure rather than trust. The organizing principle is that the same input gives the same output,
and that the quality metric cannot be fudged.

## Architecture

**Analysis layer.** Compiler accurate symbol resolution, call graphs, and control flow graphs. The
system reasons about real program structure instead of treating code as text.

**Generation layer.** Local models through Ollama, with separate models for planning and for code,
run at temperature 0 with a fixed seed. There is also a deterministic template path that needs no
model at all.

**Verification layer.** Generated projects have to build and pass their tests. Then the analysis
half rereads the generated code and reports what it finds, which catches problems a compiler
cannot see.

**Benchmark harness.** Frozen baselines and regression gates. A parser change that lowers
resolution recall on the committed COBOL baseline fails the gate instead of being found later.

**Orchestration.** Retries, structured output constraints, and model keep alive so a model reload
does not land in the middle of a run.

## Decisions worth defending

**Local first.** Privacy and repeatability instead of the convenience of a hosted API. The whole
pipeline runs on your hardware.

**Determinism.** Temperature 0 and a fixed seed. This is what makes benchmarking mean anything. You
want to measure the system, not sample noise.

**Two specialised models instead of one general one.** Planning and writing code are different
jobs, and specialising improves both. The cost is a real problem: two models competing for 16 GB.
The system handles it with keep alive and timeout tuning, and the writeup measures what that costs.

**An objective quality metric, and a correction to it.** The bar is whether the code builds and
passes tests, which beats a perplexity proxy. But the first version of that metric was useless.
When a model written operation fails the compile gate, it is replaced with an explicit
`not implemented` stub, and stubs compile. So the pass rate was 100 percent by construction.

What gets measured now is how much real logic survived the gate rather than falling back to a stub,
plus the repair counts. Finding that out and writing it down is the more useful half of this.

## Results

The inference tuning work covers GPU layer offload, output streaming, quantization treated as a
measured variable, and the two model VRAM problem:

→ [Tuning local LLM inference for a code engine](../../writeups/02-gen-system-inference-optimization.md)

The benchmarking method behind it, with frozen baselines and gates, is its own writeup:

→ [Reproducible benchmarking and regression gates](../../writeups/03-reproducible-benchmarking.md)

## Stack

Go. Local LLMs through Ollama, with a planner model and a coder model. Compiler accurate analysis
covering symbol resolution, call graphs, and control flow graphs. Deterministic generation. A
benchmark harness with regression gating.

## What is not here, and why

The implementation, the prompts, the templates, and the configuration are left out on purpose.

The architecture above and the linked writeups are enough to judge the engineering and to talk
about it in depth. More is available on request.
