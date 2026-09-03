#!/usr/bin/env python3
"""
fill_portfolio.py: auto-fill the public portfolio from your PRIVATE repos and benchmark results.

Run this ON YOUR BOX (where gen-system and HieuLuat source live). It never copies source
into the portfolio. It only extracts statistics and injects them into marked spots.

What it does:
  1. Repo stats (from git + filesystem): release/tag count, file counts, LOC.
  2. Environment capture: GPU (nvidia-smi), installed Ollama models -> benchmarks/ENVIRONMENT.md
  3. Measured results: renders any non-empty tables from benchmarks/results/measured.json
     into the writeups (between <!--measured:...--> markers).
  4. Prompts once for your LinkedIn handle (used in index.html), skippable.

Usage:
  python3 tools/fill_portfolio.py --gen-system ~/code/gen-system --hieuluat ~/code/hieuluat --beastwarden ~/code/beastwarden
  python3 tools/fill_portfolio.py --check          # show what is filled / still missing
  (run from anywhere; the portfolio root is inferred from the script location)

Safe to re-run any time: all injections are idempotent (markers stay in place).
Python 3.8+, stdlib only.
"""

import argparse, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------------- helpers

def run(cmd, cwd=None):
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None

def set_stat(text, key, value):
    """Replace <!--stat:key-->...<!--/stat--> inner value. Returns (text, changed)."""
    pat = re.compile(r"(<!--stat:%s-->)(.*?)(<!--/stat-->)" % re.escape(key), re.S)
    if not pat.search(text):
        return text, False
    new = pat.sub(lambda m: m.group(1) + str(value) + m.group(3), text)
    return new, new != text

def fmt_int(n):
    return f"{n:,}" if isinstance(n, int) else str(n)

def loc_count(repo, exts):
    total, files = 0, 0
    skip_dirs = {".git", "node_modules", "vendor", "dist", "build", "__pycache__", ".venv", "venv"}
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for f in filenames:
            if any(f.endswith(e) for e in exts):
                files += 1
                try:
                    with open(Path(dirpath) / f, "rb") as fh:
                        total += sum(1 for _ in fh)
                except OSError:
                    pass
    return files, total

def repo_stats(path, label):
    p = Path(path).expanduser()
    if not p.is_dir():
        print(f"  !! {label}: path not found: {p}")
        return None
    tags = run(["git", "tag"], cwd=p)
    commits = run(["git", "rev-list", "--count", "HEAD"], cwd=p)
    first = run(["git", "log", "--reverse", "--format=%as", "-1"], cwd=p)
    last = run(["git", "log", "--format=%as", "-1"], cwd=p)
    stats = {
        "path": str(p),
        "releases": len(tags.splitlines()) if tags else None,
        "commits": int(commits) if commits and commits.isdigit() else None,
        "first_commit": first, "last_commit": last,
    }
    print(f"  {label}: releases={stats['releases']} commits={stats['commits']} "
          f"({stats['first_commit']} → {stats['last_commit']})")
    return stats

# ----------------------------------------------------------------------------- measured tables

def render_table(section, title):
    cols = section.get("_columns", [])
    rows = section.get("rows", [])
    if not rows:
        return ""
    header = "| " + " | ".join(c.replace("_", " ") for c in cols) + " |"
    sep = "|" + "---|" * len(cols)
    def cell(x):
        return "n/a" if x is None else str(x)
    body = "\n".join("| " + " | ".join(cell(x) for x in r) + " |" for r in rows)
    # WP4: every table carries its provenance (date, commit, task set) so a
    # reader can tie the numbers to a run. Written by bench/summarise.py.
    prov = section.get("_provenance") or {}
    prov_line = ""
    if prov:
        commit = str(prov.get("gen_system_commit", ""))[:12]
        bits = [b for b in (prov.get("date"), f"commit `{commit}`" if commit else "",
                            prov.get("task_set")) if b]
        prov_line = f"\n*Measured {' · '.join(bits)}.*\n"
    return f"\n**{title}**\n\n{header}\n{sep}\n{body}\n{prov_line}"

def inject_measured(md_path, marker, blocks):
    text = md_path.read_text(encoding="utf-8")
    pat = re.compile(r"(<!--measured:%s-->)(.*?)(<!--/measured-->)" % marker, re.S)
    if not pat.search(text):
        print(f"  !! marker measured:{marker} not found in {md_path.name}")
        return False
    content = "".join(blocks).strip()
    if not content:
        return False
    payload = ("\n### Measured results\n\n"
               "*Rendered from `benchmarks/results/measured.json`. Every number below "
               "comes from the project's own harness on the hardware described above.*\n"
               + "".join(blocks) + "\n")
    new = pat.sub(lambda m: m.group(1) + payload + m.group(3), text)
    if new != text:
        md_path.write_text(new, encoding="utf-8")
        print(f"  injected measured results into {md_path.name}")
    return True

# ----------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen-system", help="path to the private gen-system repo")
    ap.add_argument("--hieuluat", help="path to the private HieuLuat repo")
    ap.add_argument("--beastwarden", help="path to the private Beastwarden repo")
    ap.add_argument("--linkedin", help="your LinkedIn handle (skips the prompt)")
    ap.add_argument("--check", action="store_true", help="report fill status, change nothing")
    args = ap.parse_args()

    md_targets = [ROOT / "projects/gen-system/README.md",
                  ROOT / "projects/hieuluat/README.md",
                  ROOT / "projects/beastwarden/README.md"]
    w01 = ROOT / "writeups/01-hieuluat-retrieval-optimization.md"
    w02 = ROOT / "writeups/02-gen-system-inference-optimization.md"

    # ---------- check mode ----------
    if args.check:
        unfilled = []
        for f in md_targets + [w01, w02, ROOT / "index.html"]:
            t = f.read_text(encoding="utf-8")
            for m in re.finditer(r"<!--stat:(\w+)-->(.*?)<!--/stat-->", t, re.S):
                if m.group(2).strip() in {"", "—", "-"}:
                    unfilled.append(f"{f.relative_to(ROOT)} :: {m.group(1)}")
            for m in re.finditer(r"<!--measured:(\w+)-->(\s*)<!--/measured-->", t):
                unfilled.append(f"{f.relative_to(ROOT)} :: measured:{m.group(1)} (empty)")
            if "YOUR-LINKEDIN" in t:
                unfilled.append(f"{f.relative_to(ROOT)} :: LinkedIn handle")
        print("Unfilled:" if unfilled else "Everything is filled. Ready to publish.")
        for u in unfilled:
            print("  -", u)
        return

    print("== Portfolio auto-fill ==\nRoot:", ROOT)

    # ---------- 1. repo stats ----------
    stats = {}
    if args.gen_system:
        g = repo_stats(args.gen_system, "gen-system")
        if g:
            go_files, go_loc = loc_count(g["path"], [".go"])
            stats.update(gen_releases=g["releases"], gen_go_files=fmt_int(go_files),
                         gen_go_loc=fmt_int(go_loc))
            stats["_gen"] = g
    if args.hieuluat:
        h = repo_stats(args.hieuluat, "hieuluat")
        if h:
            _, py_loc = loc_count(h["path"], [".py"])
            stats.update(hl_py_loc=fmt_int(py_loc))
            stats["_hl"] = h
    if args.beastwarden:
        b = repo_stats(args.beastwarden, "beastwarden")
        if b:
            ts_files, ts_loc = loc_count(b["path"], [".ts"])
            test_files, _ = loc_count(b["path"], [".test.ts"])
            stats.update(bw_ts_files=fmt_int(ts_files - test_files),
                         bw_test_files=fmt_int(test_files),
                         bw_ts_loc=fmt_int(ts_loc))
            # tests-green count: parse the repo's own HANDOFF.md baseline claim
            hp = Path(b["path"]) / "HANDOFF.md"
            if hp.exists():
                m = re.search(r"(\d[\d,]*)\s+tests\s+green", hp.read_text(encoding="utf-8", errors="ignore"))
                if m:
                    stats["bw_tests_green"] = m.group(1)
            stats["_bw"] = b

    # ---------- 2. measured.json (corpus stats + tables) ----------
    mj_path = ROOT / "benchmarks/results/measured.json"
    mj = {}
    if mj_path.exists():
        try:
            mj = json.loads(mj_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"measured.json is not valid JSON: {e}")
    hl = mj.get("hieuluat", {})
    if hl.get("corpus_documents"):
        stats["hl_documents"] = fmt_int(hl["corpus_documents"])
    if hl.get("corpus_chunks"):
        stats["hl_chunks"] = fmt_int(hl["corpus_chunks"])

    # ---------- 3. inject stat markers ----------
    for f in md_targets:
        text = f.read_text(encoding="utf-8")
        changed = False
        for k, v in stats.items():
            if k.startswith("_"):
                continue
            text, c = set_stat(text, k, v)
            changed |= c
        if changed:
            f.write_text(text, encoding="utf-8")
            print(f"  updated stats in {f.relative_to(ROOT)}")

    # ---------- 4. measured tables into writeups ----------
    blocks = [render_table(hl.get("index_comparison", {}), "Vector index: recall vs latency"),
              render_table(hl.get("rerank_effect", {}), "Two-stage rerank: quality vs added latency"),
              render_table(hl.get("embedding_throughput", {}), "Embedding precision: throughput & VRAM")]
    inject_measured(w01, "hieuluat", blocks)

    gs = mj.get("gen_system", {})
    blocks = [render_table(gs.get("offload_curve", {}), "GPU-layer offload: tokens/sec vs VRAM"),
              render_table(gs.get("streaming", {}), "Streaming: time-to-first-token"),
              render_table(gs.get("quantization_sweep", {}), "Quantization sweep: speed vs VRAM vs generation quality"),
              render_table(gs.get("two_model_strategies", {}), "Two-model serving strategies"),
              render_table(gs.get("understand_public_repos", {}), "Understand benchmark: public repos at pinned commits")]
    inject_measured(w02, "gen", blocks)

    # ---------- 5. environment capture ----------
    gpu = run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
               "--format=csv,noheader"])
    ollama = run(["ollama", "list"])
    env_lines = ["# Measured Environment", "",
                 "*Auto-generated by `tools/fill_portfolio.py`. This is the machine the "
                 "benchmarks in the writeups ran on.*", ""]
    env_lines.append(f"- **GPU:** {gpu}" if gpu else "- **GPU:** (nvidia-smi not available)")
    if ollama:
        env_lines += ["- **Local models (ollama list):**", "", "```", ollama, "```"]
    for key, label in [("_gen", "gen-system"), ("_hl", "HieuLuat"), ("_bw", "Beastwarden")]:
        if key in stats:
            s = stats[key]
            env_lines.append(f"- **{label} repo:** {s['releases'] or '?'} releases, "
                             f"{s['commits'] or '?'} commits, {s['first_commit']} → {s['last_commit']}")
    (ROOT / "benchmarks/ENVIRONMENT.md").write_text("\n".join(env_lines) + "\n", encoding="utf-8")
    print("  wrote benchmarks/ENVIRONMENT.md")

    # ---------- 6. LinkedIn handle ----------
    idx = ROOT / "index.html"
    text = idx.read_text(encoding="utf-8")
    if "YOUR-LINKEDIN" in text:
        if args.linkedin is not None:
            handle = args.linkedin.strip()
        else:
            try:
                handle = input("LinkedIn handle (blank to skip): ").strip()
            except EOFError:
                handle = ""
        if handle:
            idx.write_text(text.replace("YOUR-LINKEDIN", handle), encoding="utf-8")
            print("  set LinkedIn handle in index.html")

    # ---------- 7. staleness warning ----------
    stale = [p.name for p in (ROOT / "writeups").glob("*.html")]
    if stale:
        print("\nNOTE: the .html twins of the writeups are NOT regenerated by this script:")
        for s_ in stale:
            print("   -", s_)
        print("Rebuild them from the .md sources with: python3 tools/regen_writeup_html.py "
              "(index.html links to the .html twins, so keep them).")

    print("\nDone. Run with --check to see anything still unfilled.")

if __name__ == "__main__":
    main()
