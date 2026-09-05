# gen-system: local code understanding and generation

> An AI model is a black box. gen-system makes what the model believes about your code visible.
> It checks those beliefs against a deterministic graph built from the AST, and lets you correct
> them. Then it verifies the generated output from outside. It runs entirely on your own machine. The source is
> open under Apache-2.0: `[TODO gen-system repo URL]`. This page covers the architecture and the
> reasoning.

---

## Fast facts

- **Releases shipped:** <!--stat:gen_releases-->None<!--/stat--> since November 2025, working alone
- **Engine:** Go, <!--stat:gen_go_files-->464<!--/stat--> source files, <!--stat:gen_go_loc-->97,146<!--/stat--> lines
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

An AI model is a black box. You cannot see what it believes about your code. You find out when the
output is wrong, which is the most expensive moment to find out.

gen-system attacks that from three sides.

**Make the beliefs visible.** It builds a deterministic graph from the AST: symbols, call edges,
control flow, and effects. From that graph it derives what it believes about each routine, and it
prints those beliefs. A local model can propose more. Every proposal is checked against the graph,
and a proposal that contradicts what the parser saw is marked and never used. You can correct any
belief. Only human verified beliefs steer generation.

**Ground the model in the graph, not in text.** Context for the model comes from the graph: the
architecture summary, the related routines, the verified beliefs. This is graph RAG built from the
AST, not from embeddings of text chunks.

**Verify from outside the box.** The output is compiled on its own, then built and tested, then
reread by the same deterministic engine that built the graph. That last step catches what a
compiler cannot: unresolved calls, orphan operations, a read named operation that writes.
Hallucination is caught by machinery that does not share the model's assumptions.

The proving ground is legacy code. COBOL with copybooks and CA Gen sit next to Go, Java,
TypeScript, and Python. Legacy is where nobody can say what the system does, and where a wrong
answer costs the most.

A paper in January 2026, Reliable Graph-RAG for Codebases (arXiv 2601.08773), reached the same
finding on Java. Deterministic AST graphs ground a model more reliably and more cheaply than LLM
built graphs or vector search. gen-system's first release was November 2025. It covers six
languages, and it goes past retrieval into beliefs, generation, and verification. Same idea,
arrived at independently, taken further in execution.

It also runs locally, so no code leaves the machine, and the same input gives the same output.

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

## Design decisions, and why

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

**Team conventions as a checked contract.** A team can hand the generator a style profile: naming,
folder layout, required and banned patterns, size limits, loop style, imports. The profile can be
written by hand or derived from an existing repository through the symbol graph, with the evidence
count kept next to every derived rule. The rules go into every prompt the coder model sees. After
generation, the same rules are checked over the output by the parser, with no model involved. An
operation that compiles but breaks a rule goes back to the model with the rule named. Style never
turns logic into a stub. Only the compile gate does that.

**A certificate for every campaign.** Each benchmark run ends with an attestation and a manifest.
The attestation says what ran, on which commit and machine, which runs were dropped as not measured
and why, and what did not run. The manifest lists every raw file with its hash. A number in a
writeup can be traced back to those files.

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

## Where the code is

The full source is public under Apache-2.0: `[TODO gen-system repo URL]`. That includes the six
parsers, the belief layer, the generation pipeline, the benchmark drivers under `bench/`, the
engineering docs under `docs/`, and the test suite.

Two determinism bugs found during this work are described in the inference writeup, together with
the tests that fail against the old code. They are in the repo history, not just in the writeup.
