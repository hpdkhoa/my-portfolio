# Tuning Local LLM Inference for a Code Engine

### GPU offload, streaming, quantization, and two models sharing one consumer card

> **Context:** gen-system is a local code understanding and generation engine (see
> [project README](../projects/gen-system/)). This writeup covers tuning its inference layer.
> The quality test is objective: the generated code either builds and passes its tests, or it does
> not. Section 4 explains why the obvious version of that test is useless, and what replaced it.
> The code is proprietary.

---

## 0. The machine

One consumer GPU, not a lab machine. An NVIDIA RTX 4060 Ti with 16 GB, running Ollama, with a
planner model and a coder model sharing the card.

The production roles are `qwen3:14b` for planning and `qwen2.5-coder:14b` for code. The
quantization study uses `deepseek-coder-v2:16b-lite-instruct` at Q4_K_M, Q5_K_M, and Q8_0.

Decoding is deterministic: temperature 0, seed 42, top_p 1. That is verified, not assumed.

The exact GPU, driver, and model list are captured by the harness into
[ENVIRONMENT.md](../benchmarks/ENVIRONMENT.md). Every table below carries the commit and date it
was measured at. No speed number appears in the text of this writeup. The numbers live in the
generated tables in section 6, so the words and the data cannot drift apart.

## 1. Where it started

All inference went through one client to a local Ollama runtime. The picture was consistent. It was
correct, it was deterministic, and it was completely untuned.

- **Every call waited for the whole answer.** The client blocked until generation finished. A long
  code generation paid the full wait before the first token appeared, and nothing downstream could
  start early.
- **There were no GPU controls.** The request options set temperature, seed, and top_p. Nothing set
  how the GPU ran the model. No layer offload, no context size, no batch size. The runtime ran at
  its defaults.
- **The quantization was fixed.** The model tag carried one quant. That was a choice, never a
  measurement.
- **Two models shared 16 GB.** This is why the system needs keep alive and a long timeout. A cold
  model load takes 30 to 90 seconds and could land in the middle of a run.

The correctness layer was already strong. The performance layer was untouched, and that layer is
the actual job.

## 2. Move 1: expose the GPU controls

All model traffic passes through one function. Three settings are now read from the environment and
sent with every request:

| Variable | What it controls |
|---|---|
| `OLLAMA_NUM_GPU` | How many layers run on the GPU. This is the biggest lever. With two 14B models on 16 GB, whether the layers fit or spill to the CPU is the difference between fast and unusable. |
| `OLLAMA_NUM_CTX` | Context window size. The KV cache grows with it. Prompts here are large, so this trades VRAM for capability. |
| `OLLAMA_NUM_BATCH` | Prompt processing batch size, which sets prefill speed. |

Each setting is left out of the request when its variable is unset. A machine that sets none of
them sends exactly the same request as the old client did. That property is what keeps the
measurement honest. The tuned and untuned runs differ only by the setting being tested.

The bench driver sweeps `OLLAMA_NUM_GPU` and samples peak VRAM at each step.

## 3. Move 2: stream the output

Streaming sits behind `OLLAMA_STREAM`. The reader consumes the stream and joins the fragments back
into one string. That string is identical to what the old buffered path returned.

That matters more than it sounds. Everything downstream sees the same input either way: the JSON
extraction, the rule that generated function bodies must come back alone, and the determinism
check. Transport is not allowed to change meaning. A test asserts one unique output across five
identical streamed responses.

Buffered stays the default. Streaming is opt in until the measurement says otherwise.

What gets measured is time to first token and total time, with streaming on and off, on the same
prompt, three runs each.

## 4. Move 3: quantization, and the broken metric underneath it

Quantization is an experiment here, not a fixed choice. The same model runs at Q4_K_M, Q5_K_M, and
Q8_0 on the coder role, with the planner held fixed. Each run measures speed, VRAM, and quality.

The quality axis is where this got interesting, and where the first version of this writeup was
wrong.

**The obvious metric does not work.** The plan was to report compile pass rate. Generated code
either builds or it does not. Every run came back at 100 percent.

That is not because the model is perfect. It is **by construction**. When a model written operation
fails to compile, the engine sends it back to the model with the build error. If it still fails,
the engine replaces the body with an explicit `not implemented` stub. The stub compiles. The
service always builds.

A metric that cannot go down measures nothing. A quantization that badly damaged the output would
still score 100 percent.

**What replaced it.** The instrumentation now counts what actually changes. All of it comes from
the same code path production uses:

| Metric | What it catches |
|---|---|
| `ops_stubbed` and `stub_rate_pct` | How much model written logic failed the compile gate and fell back to a stub. This is the real quality signal. |
| `op_repair_attempts` and `op_repair_successes` | Repair rounds at the operation level, capped at 2 before the stub. A weaker quant should need more. |
| `heal_attempts_total` and `heal_success` | Repair rounds at the task level, capped at 3. |
| `go_test_pass` | Whether the generated backend passes its own tests, including one that fails if an operation panics at runtime. |
| `verify_findings` | What the project's own code understanding engine finds when it rereads the generated backend: unresolved calls, orphan operations, read operations that write. |
| `prompt_tokens` and `wall_s` | Cost per run. |

Compile pass rate is still reported. It is no longer the headline, and the reason it is useless is
now written down instead of hidden.

The task set is five fixed application ideas. They were frozen and committed before the first run,
so they cannot be tuned to fit the results.

## 5. Move 4: two models, one card

Two models competing for 16 GB is a real design problem with more than one good answer. Three
strategies run against the same frozen task set:

| Strategy | What it is | What it costs |
|---|---|---|
| A. Sequential with keep alive | The production default. One model resident at a time. | A model reload when the roles swap. Measured as the load time difference. |
| B. Both resident | Keep alive never expires. Both models stay warm. | VRAM headroom, and speed under contention. Whether both even fit is itself a result. |
| C. One shared model | The coder model plans as well, so nothing ever swaps. | Planning quality, visible as stub rate, repair counts, and extra entities. |

One clarification belongs everywhere this is described. **There is no scheduler.** "Sequential
scheduling with keep alive" means Ollama's own keep alive, two model roles, and measurement of what
that costs. No scheduling code was written. Claiming otherwise would not survive a reading of the
source.

## 6. Results

<!--measured:gen-->
<!--/measured-->

> **Status:** the instrumentation, the GPU controls, the streaming path, and the five drivers are
> written and committed. The runs are still pending on the benchmark machine. Tables appear above
> as the runs land. Until a table appears, treat that move as built and not yet measured. Nothing
> here quotes a number that a run did not produce.

| Change | Effect | What is measured |
|---|---|---|
| GPU controls | Speed and fit on one card | Tokens per second and peak VRAM against offloaded layers |
| Streaming | Lower time to first token | Time to first token and total time, on and off, three runs |
| Quantization | Speed and VRAM against quality | Speed, VRAM, stub rate, repair counts, test pass |
| Two model strategies | Serving without reloads | Reload cost, speed, stub rate across three strategies |

## 7. Future work

Two directions, neither of them claimed as done.

The first is serving the same model through a production inference engine, with continuous batching
and paged attention. Then compare it against the Ollama baseline on the same harness. That
comparison is close to the day job, and it makes the batching and KV cache trade offs concrete.

The second is feeding the rendered control flow graphs back to the model as repair context, behind
a flag, and measuring it properly. I expect no effect on Go repair, because the compiler already
tells the model what is wrong. I expect a possible effect on COBOL and on belief enrichment, where
there is no compiler to lean on. The result gets published either way, including if it is null.

## 8. What I would want a reader to take from this

Not "I tuned some settings." The untuned runtime was an opportunity. Each control became a measured
experiment. When the headline quality metric turned out to be 100 percent by construction, the
response was to say so and build a metric that can move.

The broken metric was not the only thing this pass turned up. The rest is the part I would actually
want read.

**Two determinism bugs, found by reading my own code.** Neither came from a bug report. Determinism
is the load bearing claim of this system: temperature 0, fixed seed, identical output. Symbol
resolution broke it. It took the first match while walking a Go map, and Go randomizes that order.
Two exported symbols sharing a short name could resolve differently between runs, and the call
graph quietly changed shape.

I fixed it, wrote tests, and moved on. Then it turned out there was a second resolver on a
different code path with the same flaw, plus a worse one. It had no tier preference at all, so a
standard library symbol could capture a project call. My tests had gone through the fixed path and
passed while the bug sat next door. The second fix deletes the duplicate rather than repairing it.
Two functions answering the same question differently is how the split happened.

**Six tests that passed for the wrong reason.** A group of frontend tests had been failing. My first
read was that they looked environmental. They were not. Three failed because a test helper matched
nodes by name, while call nodes carry their identifier in a different field. Every lookup silently
found nothing, and a correct frontend took the blame. Two were a formatting artifact that rendered
a flowchart label as broken text. One asserted a rule that a later version had deliberately
replaced. Only one was genuinely platform specific.

Both stories have the same shape, and that shape is the point. **The failure was not a wrong
answer. It was a confident one.** A metric stuck at 100 percent. A test suite that was green on the
path I happened to test. Six red tests I was ready to explain away as someone else's problem.

None of that is caught by running the thing and watching it work. It is caught by going back and
asking what each number would look like if it were lying to you. The benchmark figures below are
only worth what that habit is worth.

*All timings are native local GPU measurements taken through the project's own harness, on the
machine described in section 0. Absolute speed depends on the GPU. The shape of each trade off is
the part that transfers. See [reproducible benchmarking](03-reproducible-benchmarking.md).*
