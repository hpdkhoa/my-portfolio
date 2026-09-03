# Beastwarden: a deterministic tactics roguelite

> A browser based turn based grid tactics game in TypeScript, using Vite and Pixi. The simulation
> core is pure, seeded, and deterministic. The test suite enforces the design rather than
> describing it.
>
> It is also a demonstration of something my other projects only claim: directing AI assisted
> development under strict rules that a machine checks. The source is private while the game is in
> development. This page covers the architecture and the working discipline.

---

## Fast facts

- **Engine:** TypeScript, <!--stat:bw_ts_files--><!--/stat--> source files,
  <!--stat:bw_ts_loc--><!--/stat--> lines. Vite and Pixi web client
- **Tests:** <!--stat:bw_test_files--><!--/stat--> test files,
  <!--stat:bw_tests_green-->1,993<!--/stat--> passing at the last verified baseline
- **Core purity:** no DOM, no `Date.now`, no `Math.random` in the simulation core. This is enforced
  by lint rules and custom guards, not by convention
- **Determinism:** the same seed gives the same everything. The battle forecast must equal what the
  dice actually do
- **Process:** a roadmap of bounded work packages, and a verify gate that must pass before any
  session ends: typecheck, lint, custom guards, the full test run, and a build

## The ideas worth discussing

**A pure deterministic core, enforced by tooling.** The simulation in `src/core` is a pure function
of state and seed. That is not a style preference. It is what makes a forecast system honest.

The interface can predict a battle outcome by running the same core the battle itself will run. A
test then asserts that the prediction and the real roll never disagree. This is the same principle
as gen-system's temperature 0 generation. Determinism is what makes a test mean something.

**Rules as guards, not comments.** Two custom guards run in CI next to lint and typecheck.

The first bans the "is dead" flag pattern outright. Death is deletion. An entity that no longer
exists cannot be half alive somewhere else in the state.

The second flags any exported symbol that nothing outside the tests imports. It ratchets down from
an explicit allow list, so unused public surface cannot quietly pile up.

A rule a reviewer has to remember is a rule a machine should check instead.

**Closed unions instead of open plugins.** Adding new content, such as a skill, is pure
configuration. Adding a new kind of effect or dice rule is a code change. Every handler that
switches on that type has to acknowledge it before the build passes.

The compiler enumerates the design space. Adding a case without handling it everywhere is a type
error, not a runtime surprise.

**AI assisted, human directed, with the discipline written down.** The game is built in bounded
work packages across AI assisted sessions, under a standing agreement.

The rules above are not negotiable. Every session ends with the full verify gate green. Progress
ledgers get updated, so the next session starts from verified truth instead of optimistic memory.

This is the practical shape of keeping a human in the loop of agentic engineering. My other work
addresses the same problem from the tool side. Here I am experiencing it from the director's chair.

## Why it belongs in this portfolio

It is a third independent demonstration of the same idea as HieuLuat and gen-system: design the
correctness properties in, then have machinery enforce them. Different language, different domain,
different rendering stack, same thesis.

It is also the rare artifact a reviewer can feel. The determinism claim stops being a bullet point
when the damage forecast you hovered over is exactly what the dice then do.

## Stack

TypeScript. Vite. Pixi for WebGL 2D. Vitest. Custom lint guards. A seeded random number generator
in the simulation core. DragonBones for skeletal animation.

## What is not here, and why

The game is in active development, so the source, the content, and the design documents stay
private for now.

A playable build is available on request. As with the other projects, the architecture above is
written to be defended line by line in a technical conversation.
