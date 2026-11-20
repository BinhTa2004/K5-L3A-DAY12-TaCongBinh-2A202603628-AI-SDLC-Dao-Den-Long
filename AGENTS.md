# Đảo Đèn Lồng — Phase 2

- Read both phase requirements, `docs/requirements/phase-2-standard.md` and `game.contract.json` before changing rules. Ticket-02 supersedes Phase 1 tuning.
- `src/core.js` is the only gameplay implementation; browser and Python/QuickJS use it unchanged.
- Build: `python -m pip install -r requirements.txt`. Play: `python tools/serve.py`.
- Verify: `python tools/verify.py --phase phase-2`. Never claim success with a failing check.
- Run at fixed 60 Hz; distances use XZ, inclusive radius; snapshot zero precedes input.
- Never use wall time or Math.random in gameplay. Scenario construction awards no points/events.
- Preserve the mandatory tick order: pause, timers, motion/fall, pickups, deposit, safe zones, pulse, actors, theft then hits, spawn, outcome.
- Dash lasts 12 ticks; pulse push lasts 15; fall ignores invulnerability and waits 60 ticks before respawn.
- Keep evidence from actual commands in `docs/proof/phase-2`; never overwrite the Phase 1 tag/evidence.
- GUI-only settings/audio/campaign need browser checks; a headless pass does not prove UI behavior or FPS.
- Use `.agents/skills/verify-game/SKILL.md` when collecting evidence.
