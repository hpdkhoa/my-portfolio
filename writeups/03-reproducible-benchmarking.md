# Reproducible Benchmarking & Regression Gating

### The methodology that makes every other result in this repo trustworthy

> **Why this matters:** an optimization without a before-number is a guess, and a benchmark you
> can't reproduce is an anecdote. Both HieuLuat and gen-system are tuned against fixed,
> repeatable measurements rather than impressions. This writeup is the methodology those
> results rest on — and, honestly, it's the habit that separates engineers who *claim* speedups
> from engineers who *prove* them.

---

## 1 · The principle

Performance work is only as credible as its measurement. Three rules govern all the optimization in this repo:

1. **Measure before *and* after, always.** Every change is reported as a delta against a recorded baseline. No baseline, no claim.
2. **Make runs deterministic where possible.** Reproducibility is what turns a measurement into evidence — you're measuring the system, not sampling noise.
3. **Anchor quality to an objective metric.** Speed at the cost of silent quality loss is a regression, so quality must be measured alongside performance, not assumed constant.

## 2 · Frozen baselines

A baseline is a **recorded, version-tagged measurement** of the system before a change — captured under fixed conditions and stored, not re-derived from memory. Every optimization in the two projects is reported against one. This is what lets a statement like "this change improved throughput" be checked rather than trusted.

## 3 · Regression gates

The stronger version of "measure after" is to make regressions **fail automatically**. In gen-system, a change that lowers the **compile-and-test pass rate** is caught by a gate, not discovered weeks later in production. The gate treats a quality drop as a build failure. This is unusual and valuable: it means performance work can proceed aggressively *because* a quality regression can't slip through silently.

The same discipline applies to HieuLuat's **labeled eval suites** (citation-QA, definition-lookup, and others): an optimization to the retrieval path is accepted only if it holds or improves the measured quality on those fixed cases. A faster index that quietly drops recall on the eval set is rejected, not shipped.

## 4 · Determinism

Where the workload allows it, runs are made deterministic — for example, gen-system generates at temperature 0 with a fixed seed. The payoff is that benchmark numbers are stable across runs, so a delta reflects the change you made, not stochastic variation. (For genuinely stochastic components, the answer is repeated runs and reporting the distribution, not a single number.)

## 5 · The objective-quality advantage

The most useful thing about both projects' metrics is that quality is **objective**, not proxied:

- **gen-system:** does the generated code *compile and pass tests*? A binary, domain-meaningful signal.
- **HieuLuat:** does the answer stay grounded and cite correctly on labeled legal QA cases?

This matters most for **quantization and approximation** work, where the whole risk is silent quality loss. Most inference write-ups can only show a perplexity curve and hope it correlates with usefulness. Here, the quality cost of a 4-bit quant shows up directly as a drop in pass rate — so the trade-off is *visible* and the decision is *defensible*.

## 6 · How this shows up in the other writeups

- The [retrieval optimization](01-hieuluat-retrieval-optimization.md) recall-vs-latency curves and reranker quality lifts are all measured against the eval suites under this methodology.
- The [inference optimization](02-gen-system-inference-optimization.md) tokens/sec, VRAM, and compile-pass-rate numbers all run through the benchmark harness with frozen baselines and gates.

## 7 · What I'd want a reader to take from this

Reproducible measurement isn't bureaucracy — it's what makes everything else in this repo *evidence* instead of *assertion*. I build the baseline first, gate on an objective quality metric, and keep runs deterministic, so that when I say "N× faster with quality held," there's a number behind every word of it.

*Note: this writeup describes methodology; specific figures live in the project-specific writeups and depend on hardware. The methodology is the transferable part.*
