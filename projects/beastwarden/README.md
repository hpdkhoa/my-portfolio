# Beastwarden — A Deterministic Tactics Roguelite (and a disciplined AI-assisted build)

> A browser turn-based grid-tactics roguelite in **TypeScript** (Vite + Pixi) with a **pure,
> seeded, deterministic core** and a test suite that enforces the design instead of describing it.
> Also a demonstration of something my other projects claim in the abstract: **directing
> AI-assisted development under strict, machine-enforced invariants.** Source is private while the
> game is in active development; this is the architecture and the engineering discipline.

---

## Fast facts

- **Engine:** TypeScript — <!--stat:bw_ts_files-->193<!--/stat--> source files, <!--stat:bw_ts_loc-->74,907<!--/stat--> lines · Vite + Pixi web client
- **Tests:** <!--stat:bw_test_files-->249<!--/stat--> test files, <!--stat:bw_tests_green-->2833<!--/stat--> tests green at last verified baseline
- **Core purity:** no DOM, no `Date.now`, no `Math.random` in the simulation core — **lint- and guard-enforced**, not convention
- **Determinism:** same seed → same everything; the battle **forecast oracle must equal the actual roller**
- **Process:** work-package roadmap, session verify gate (typecheck · lint · custom guards · full test run · build) before any session ends

## The engineering ideas worth discussing

**A pure deterministic core, enforced by tooling.** The simulation (`src/core`) is a pure function
of state and seed. That's not a style preference — it's what makes a forecast system honest: the
UI can *predict* a battle outcome by running the same core the battle will run, and a test asserts
the oracle and the roller never disagree. It's the same principle as gen-system's temp-0/fixed-seed
generation: determinism is what makes testing *mean* something.

**Invariants as guards, not comments.** Two custom guards run in CI alongside lint and typecheck:
one bans the `isDead`-flag anti-pattern outright (death is deletion — an entity that no longer
exists cannot be half-alive anywhere in the state), and one flags any exported symbol with no
non-test importer, ratcheting from an explicit allow-list so dead public surface can't silently
accumulate. Rules a reviewer would have to remember are rules a machine checks instead.

**Closed unions over open plugins.** New content (a skill) is pure configuration; a new *kind* of
effect or dice rule is a code change that every exhaustive handler must acknowledge before the
build passes. The compiler enumerates the design space — adding a case without handling it
everywhere is a type error, not a runtime surprise.

**AI-assisted, human-directed — with the discipline written down.** The game is built in bounded
work packages across AI-assisted sessions, under a standing contract: the invariants above are
non-negotiable, every session must end with the full verify gate green, and progress ledgers are
updated so the next session starts from verified truth rather than optimistic memory. This is the
practical shape of "human-in-the-loop agentic engineering" — the same problem my AI-platform work
addresses from the tool side, experienced here from the director's chair.

## Why it's in an AI/systems portfolio

Because it's a third independent demonstration of the same thesis as HieuLuat and gen-system —
**correctness properties designed in, then enforced by machinery** — in a different language,
domain, and rendering stack. And because a playable game is the rare artifact a reviewer can
actually *feel*: the determinism claim isn't a bullet point when the damage forecast you hovered
is exactly what the dice then do.

## Stack

TypeScript · Vite · Pixi (WebGL 2D) · Vitest · custom lint guards · seeded PRNG simulation core ·
DragonBones runtime for skeletal animation.

## What's not here (and why)

The game is in active development, so source, content, and design documents stay private for now.
A playable build is available on request — and the architecture above is, as with the other
projects, written to be defended line-by-line in a technical conversation.
