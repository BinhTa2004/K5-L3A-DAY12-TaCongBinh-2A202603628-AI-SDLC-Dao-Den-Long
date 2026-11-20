---
name: verify-game
description: Run deterministic headless regression and capture reproducible evidence for a Lantern Island phase before tagging it.
---

Run `python tools/verify.py --phase phase-2` from the repo root.
The command must return zero before declaring verification passed or creating a phase tag.
Read `docs/proof/phase-2/report.json` and the test log; do not hand-edit outputs.
Inspect the browser at 1280x720 for camera, HUD, restart and the character's hat.
Store screenshots separately from headless evidence. Report browser checks as pending if unavailable.
When changing a game rule, add a scenario that observes its consequence; run regression again.

Phase 2: inspect feature outputs (dash, charm, drifter theft/drop, pause, pad, wind, respawn).
Run python tools/browser_check.py --phase phase-2 after UI changes; verify campaign, persistent settings and real FPS at 1280x720.
Keep Phase 1 evidence unchanged; report measured GPU and per-night FPS rather than assuming performance.
