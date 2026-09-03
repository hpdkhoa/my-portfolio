# Snippets: small runnable examples

These are small Python files that run on their own with toy data. They show techniques used in the
projects. They contain none of the production code, prompts, data, or configuration from HieuLuat
or gen-system.

They exist so the ideas in the writeups are easy to check without exposing anything private.

Each file runs with a standard Python 3 install. Only the standard library is needed, plus NumPy
where noted. No GPU, database, or network required.

| File | What it shows | From |
|---|---|---|
| `toy_retrieval.py` | Retrieve then rerank over fake vectors, and why you must check an index's recall | [retrieval optimization](../writeups/01-hieuluat-retrieval-optimization.md) |
| `roofline_demo.py` | Naive against blocked matrix multiply, and the memory versus compute intuition | [inference optimization](../writeups/02-gen-system-inference-optimization.md) |

Run either one directly:

```bash
python3 toy_retrieval.py
python3 roofline_demo.py
```

> These are teaching examples, not the systems. HieuLuat's implementation is proprietary.
> gen-system's is open source under Apache-2.0. The point is to make the claims in the writeups
> concrete enough to check.
