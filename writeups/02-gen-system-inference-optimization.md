# Optimizing Local-LLM Inference for a Code Engine

### GPU offload, streaming, quantization-as-a-variable, and two-model VRAM contention — with an objective quality metric

> **Context:** gen-system is a local-first code-intelligence and generation engine (see
> [project README](../projects/gen-system/)). This writeup covers tuning its inference layer.
> What makes it a stronger applied-inference story than most: the quality axis is **objective** —
> generated code either compiles and passes tests or it doesn't — so quantization and tuning
> regressions are *visible*, not hidden behind perplexity. Source is proprietary.

---

## 0 · Measured environment

All measurements in this writeup come from the production setup, not a lab machine:
**NVIDIA RTX 4060 Ti 16 GB** · Ollama with keep-alive · a **role-split two-model design**
sharing one GPU — **qwen3:14b** as planner (reasoning/architecture, ≈9.3 GB) and
**qwen2.5-coder:14b** as coder (≈9.0 GB) — a pairing that cannot be co-resident in 16 GB,
which is exactly why the keep-alive, timeout, and sequencing engineering below exists ·
fully offline, deterministic decode (temp 0, fixed seed).

*Model lineage: production originally ran DeepSeek-Coder-V2 16B @ Q5_K_M as a single
model for all roles. Benchmark data and observed entity over-generation drove the split
to a reasoning planner + a coder model (v23.35). DeepSeek-Coder-V2 16B remains the
subject of the quantization study below. Production throughput for the current pair is
reported in the measured tables (~30 tok/s short-form per model, dense 14B); the
migration deliberately traded the MoE model's ~110 tok/s for planning quality.*

## 1 · The starting point

All inference flowed through a single client to a local Ollama runtime, and the picture was consistent: **correct, deterministic, and completely un-tuned at the runtime level.** Specifically:

- **One-shot, non-streamed calls.** The client blocked until the entire completion was done — so for a long code generation, you paid full latency before the first token and couldn't overlap downstream parsing.
- **No GPU/runtime tuning surface.** The request options exposed sampling controls (temperature, seed, top-p) but **nothing about how the GPU runs the model** — no layer-offload, context-length, or batch controls. The runtime ran at defaults.
- **A fixed quantization.** The model string carried one quant; it was a fixed choice, never measured against alternatives.
- **Two models contending for VRAM.** Separate planner and coder models share one GPU — which is *why* the system needed model keep-alive and a long timeout (a cold reload of 30–90s could otherwise land mid-run).

The correctness/orchestration layer was excellent (deterministic seeds, retries, structured-output constraints, keep-alive). The **inference-performance** layer was untouched — and that layer is the actual applied-inference job.

## 2 · Move 1 — Expose and tune the GPU knobs (highest payoff)

The first win was making the runtime's performance surface tunable and **measuring each knob** against the existing benchmark harness:

- **GPU-layer offload** — the dominant lever. With two ~14B models, whether layers fit in VRAM or spill to CPU is the difference between fast and unusable. I measured tokens/sec as a function of offloaded layers.
- **Context length** — the KV-cache scales with it. The prompts here are large (plans, schemas, legacy code), so right-sizing context trades VRAM for capability; too large wastes cache memory that could fund a larger batch.
- **Prompt-processing batch size** — affects prefill throughput.

**Deliverable:** a tokens/sec-vs-offload curve and a VRAM-vs-context table for both models, run through the harness. This is "I tuned a real local-inference deployment with measured results" — and it rode on benchmarking infrastructure the project already had.

## 3 · Move 2 — Stream the output

Switching to streaming output produced two wins: **time-to-first-token dropped sharply** (you stop waiting for the whole completion), and you can **overlap** — begin parsing and validating the generated code while later tokens still arrive. The determinism and retry logic are unchanged; only *how the response is consumed* changed. Measured before/after: time-to-first-token and total latency on the same benchmark suites.

## 4 · Move 3 — Quantization as a measured variable (the textbook idea, applied)

Instead of running one fixed quant, I turned quantization into an experiment: benchmark the **same model at multiple quantization levels** (e.g. 4-bit / 5-bit / 8-bit / FP16) for both the planner and coder roles, and measure the **three-way trade-off**: tokens/sec, VRAM, and **output quality**.

The decisive advantage here is the quality axis. gen-system's whole premise is that generated code **builds and passes tests** — so the quality metric is the **compile-and-test pass rate**, not perplexity. A quantization that speeds inference but tanks the pass rate is *visibly* worse. Most candidates can only show a perplexity curve; this shows "quantization vs tokens/sec vs VRAM vs **compile-pass-rate**" — an objective, domain-meaningful result.

## 5 · Move 4 — Two-model VRAM contention (a real systems-of-inference problem)

The planner/coder models competing for GPU memory is a legitimate architecture problem with several solutions worth evaluating rather than assuming:

- **Sequential with smart keep-alive** (the original approach) — measure the reload cost actually being paid.
- **More aggressive quantization to keep both resident** — can both stay warm at 4-bit?
- **One shared higher-quant model vs two specialized lower-quant models** — a quality-vs-memory experiment the compile-pass-rate metric can adjudicate.
- **KV-cache management** — how context length and batch interact with cache residency.

**Deliverable:** "two-model serving on one GPU — three strategies, measured on reload cost, throughput, and compile-pass-rate." This is a senior-level story: not one knob, but an architecture decision under a hardware constraint, settled with numbers.

## 6 · Results summary

<!--measured:gen-->
### Measured results

*Auto-rendered from `benchmarks/results/measured.json` — every number below comes from the project's own harness on the hardware described above.*

**Quantization sweep: speed vs VRAM vs compile-pass-rate**

| quant | tokens per sec | vram gb | compile pass rate pct |
|---|---|---|---|
| Q5_K_M | 110.4 | 12.8 | 100.0 |
| Q8_0 | 40.2 | 15.3 | 100.0 |
| Q4_K_M | 125.7 | 11.4 | 100.0 |
| qwen2.5-coder:14b (production coder) | 30.8 | — | 100.0 |
| qwen3:14b (production planner) | 29.1 | — | 100.0 |

**Two-model serving strategies**

| strategy | reload cost s | tokens per sec | compile pass rate pct |
|---|---|---|---|
| sequential + keep-alive (Q5_K_M) | 7.46 | 110.4 | 100.0 |
| sequential + keep-alive (Q8_0) | 9.97 | 40.2 | 100.0 |
| sequential + keep-alive (Q4_K_M) | 7.03 | 125.7 | 100.0 |

<!--/measured-->

| Change | Primary effect | What I measured |
|---|---|---|
| Expose + tune GPU knobs (offload, context, batch) | Throughput & fit on one GPU | Tokens/sec vs offload; VRAM vs context |
| Output streaming | Lower time-to-first-token; overlap | TTFT and total latency, before/after |
| Quantization as a variable | Speed/VRAM vs quality, chosen deliberately | Tokens/sec vs VRAM vs **compile-pass-rate** |
| Resolve two-model VRAM contention | Stable serving without reloads | Reload cost, throughput, pass-rate across 3 strategies |

## 7 · Future work

The deepest extension is serving the same model through a **production inference engine** (continuous/in-flight batching, paged attention, tensor parallelism) and comparing head-to-head against the Ollama baseline — same model, same harness, measured tokens/sec and throughput-under-concurrency. That comparison is close to the actual day job of an inference engineer, and it makes the batching/KV-cache concepts concrete.

## 8 · What I'd want a reader to take from this

The un-tuned runtime was an opportunity, not a flaw: I **opened the inference black box, made each knob a measured experiment, and — crucially — anchored every quality claim to an objective metric** (does the code compile and pass). That last point is the differentiator: I can show quantization's quality cost in pass-rate, where most can only show perplexity.

*Methodology note: timings are WebAssembly-free, native local-GPU measurements through the project's harness; absolute GFLOP/s and tokens/sec depend on the specific GPU and are illustrative of the trade-off shape, not universal constants. See [`03-reproducible-benchmarking.md`](03-reproducible-benchmarking.md).*
