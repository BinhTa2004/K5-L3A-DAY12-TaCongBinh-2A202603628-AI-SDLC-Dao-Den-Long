---
name: verify-game
description: Run deterministic headless regression and capture reproducible evidence for a Lantern Island phase before tagging it.
---

Run `python tools/verify.py --phase phase-1` from the repo root.
The command must return zero before declaring verification passed or creating a phase tag.
Read `docs/proof/phase-1/report.json` and the test log; do not hand-edit outputs.
Inspect the browser at 1280x720 for camera, HUD, restart and the character's hat.
Store screenshots separately from headless evidence. Report browser checks as pending if unavailable.
When changing a game rule, add a scenario that observes its consequence; run regression again.
