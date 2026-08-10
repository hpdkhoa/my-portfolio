# Snippets — runnable, non-proprietary illustrations

These are small, **self-contained** Python files that demonstrate *techniques* used in the
projects, written to run on their own with toy data. They deliberately contain **none** of the
production code, prompts, data, or configuration from HieuLuat or gen-system — they exist so the
*ideas* in the writeups are legible and verifiable without exposing anything proprietary.

Each file runs with a standard Python 3 install (only the standard library + NumPy where noted);
no GPU, database, or network required.

| File | Illustrates | From writeup |
|---|---|---|
| `toy_retrieval.py` | Two-stage retrieve-then-rerank over fake vectors, and why an ANN index's recall must be checked | [retrieval optimization](../writeups/01-hieuluat-retrieval-optimization.md) |
| `roofline_demo.py` | Naive vs blocked matrix-multiply timing and the memory-vs-compute (roofline) intuition | [inference optimization](../writeups/02-gen-system-inference-optimization.md) |

Run any of them directly:

```bash
python3 toy_retrieval.py
python3 roofline_demo.py
```

> These are teaching toys, not the systems. The real implementations are proprietary and not in
> this repo. The point is to make the writeups' claims concrete and checkable.
