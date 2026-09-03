"""
roofline_demo.py: a teaching toy for the memory versus compute (roofline) intuition behind
GPU/inference optimization: naive vs blocked matrix multiply, and the O(n^3) growth pattern.

This is pure-Python (no NumPy, no GPU) so it RUNS anywhere and the *shape* of the result is
visible. Absolute speeds are irrelevant here. What matters is (a) work grows ~n^3, and
(b) improving data locality (blocking) helps, which is the same idea that makes tiled GPU
matmul and good cache behavior matter.

Run:  python3 roofline_demo.py
Deps: standard library only. (Small sizes by default so it finishes quickly.)
"""

import time
import random

random.seed(42)


def make(n):
    return [[random.random() for _ in range(n)] for _ in range(n)]


def matmul_naive(A, B, n):
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            s = 0.0
            for k in range(n):
                s += A[i][k] * B[k][j]   # B[k][j] strides down a column, so poor locality
            C[i][j] = s
    return C


def matmul_blocked(A, B, n, block=16):
    # Transpose B so the inner loop walks contiguous memory in both operands,
    # the pure-Python analogue of improving data locality / tiling.
    Bt = [[B[k][j] for k in range(n)] for j in range(n)]
    C = [[0.0] * n for _ in range(n)]
    for ii in range(0, n, block):
        for jj in range(0, n, block):
            for i in range(ii, min(ii + block, n)):
                Ai = A[i]
                Ci = C[i]
                for j in range(jj, min(jj + block, n)):
                    Btj = Bt[j]
                    s = 0.0
                    for k in range(n):
                        s += Ai[k] * Btj[k]   # both contiguous now
                    Ci[j] = s
    return C


def flops(n):
    return 2 * n ** 3   # multiply-add per inner step


print("=== O(n^3) growth: doubling n ~8x's the work ===")
print(f"{'n':>5} | {'naive (s)':>12} | {'FLOPs':>14} | {'~time ratio':>12}")
print("-" * 52)
prev = None
for n in (32, 48, 64, 96, 128):
    A, B = make(n), make(n)
    t0 = time.perf_counter()
    matmul_naive(A, B, n)
    dt = time.perf_counter() - t0
    ratio = (dt / prev) if prev else 1.0
    print(f"{n:>5} | {dt:>12.4f} | {flops(n):>14,} | {ratio:>12.2f}x")
    prev = dt

print("\nTakeaway: the time ratio tracks the (n_new/n_old)^3 work ratio, the cubic")
print("growth that makes matmul the workload GPUs (and Tensor Cores) exist to accelerate.\n")

print("=== Data locality matters: naive vs locality-improved (blocked/transposed) ===")
n = 96
A, B = make(n), make(n)

t0 = time.perf_counter(); matmul_naive(A, B, n);   t_naive = time.perf_counter() - t0
t0 = time.perf_counter(); matmul_blocked(A, B, n); t_block = time.perf_counter() - t0

print(f"n = {n}")
print(f"  naive            : {t_naive:.4f} s")
print(f"  locality-improved: {t_block:.4f} s")
print(f"  speedup          : {t_naive / t_block:.2f}x")
print("\nTakeaway: same FLOPs, better memory access pattern -> faster. On a GPU this is")
print("exactly why a TILED matmul (operands staged in fast shared memory) beats the naive")
print("version. The optimization is about moving less data, not doing less math.")
