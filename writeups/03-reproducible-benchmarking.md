# Reproducible Benchmarking and Regression Gates

### The method that makes every other number in this repo worth reading

> **Why this matters:** an optimization without a before number is a guess. A benchmark you cannot
> reproduce is a story. Both HieuLuat and gen-system are tuned against fixed, repeatable
> measurements. This writeup describes the method those results rest on.

---

## 1. The three rules

Performance work is only as good as its measurement. Three rules cover all of it.

1. **Measure before and after, every time.** Every change is reported against a recorded baseline.
   No baseline, no claim.
2. **Make runs repeatable where the work allows it.** That is what turns a measurement into
   evidence. You want to measure the system, not sample noise.
3. **Tie quality to something objective.** Speed bought with silent quality loss is not a win. So
   quality gets measured next to performance, never assumed to hold.

## 2. Frozen baselines

A baseline is a recorded measurement of the system before a change, tagged with a version and taken
under fixed conditions. It is stored, not remembered.

Every optimization in both projects is reported against one. That is what makes a sentence like
"this change improved throughput" checkable instead of something you have to take on trust.

## 3. Regression gates

The stronger version of "measure after" is to make a regression fail the build automatically.

In gen-system, a benchmark run can be diffed against a committed baseline, and a drift beyond a
tolerance exits non zero. The frozen COBOL baseline works this way. A parser change that lowers
resolution recall on 30,000 lines of third party COBOL is caught by the gate, not found weeks
later.

The same idea applies to HieuLuat's labeled evaluation sets. A change to the retrieval path is
accepted only if measured quality holds or improves on those fixed cases. A faster index that
quietly drops recall is rejected rather than shipped.

## 4. Repeatability

Where the work allows it, runs are made deterministic. gen-system generates at temperature 0 with a
fixed seed, and a suite checks that the same prompt gives one unique output across repeated runs.

The payoff is that a difference between two runs reflects the change you made, not random
variation. Where a component is genuinely random, the honest answer is repeated runs and a reported
range, not a single number.

## 5. Choosing a quality metric that can actually move

Both projects measure quality directly rather than through a proxy. That is the useful part. But
choosing the metric is harder than it looks, and gen-system got it wrong the first time.

The plan was to report compile pass rate. Does the generated code build? It came back at 100
percent on every run. Not because the model was perfect, but because the engine replaces a failing
operation with a stub that compiles. The metric could not go down, so it measured nothing.

The replacement counts what actually varies: how much generated logic survived the compile gate
rather than falling back to a stub, and how many repair rounds that took. Details are in
[section 4 of the inference writeup](02-gen-system-inference-optimization.md).

This matters most for quantization work, where the whole risk is silent quality loss. Most
inference writeups can only show a perplexity curve and hope it tracks usefulness. A metric that is
objective but stuck is worse than a proxy, because it looks like evidence. So the lesson is not
simply to pick an objective metric. It is to check that the metric can actually move.

## 6. Where this shows up

- The [retrieval optimization](01-hieuluat-retrieval-optimization.md) recall and latency curves are
  measured against the evaluation sets under this method. Section 6 there is a worked example of
  reading a flat number correctly.
- The [inference optimization](02-gen-system-inference-optimization.md) speed, VRAM, stub rate, and
  repair counts all run through the benchmark harness against frozen baselines.

## 7. What I would want a reader to take from this

Reproducible measurement is not paperwork. It is what makes the rest of this repo evidence instead
of assertion.

I build the baseline first. I commit the task set before the first run, so it cannot be tuned to
fit the results. I gate on a quality metric and keep runs repeatable. Then when I say a change made
something faster while quality held, there is a number behind every word.

The part that took longest to learn is in section 5. Having a metric is not the same as having a
metric that works.

*This writeup describes method. The figures live in the project writeups and depend on hardware.
The method is the part that transfers.*
