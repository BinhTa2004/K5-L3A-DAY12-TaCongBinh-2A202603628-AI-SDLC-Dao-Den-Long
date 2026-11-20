# Đảo Đèn Lồng — Phase 3

- Read `docs/requirements/phase-3.md`, `docs/adr/003-fuel-and-dawn.md`, and `game.contract.json` before changing rules. Ticket-03 replaces early wins, permanent light, fixed capacity and previous scoring.
- `src/core.js` is the only gameplay implementation; browser and Python/QuickJS use it unchanged.
- Build: `python -m pip install -r requirements.txt`. Play: `python tools/serve.py`.
- Verify: `python tools/verify.py --phase phase-3`. Never claim success with a failing check.
- Run at fixed 60 Hz; distances use XZ, inclusive radius; snapshot zero precedes input.
- Never use wall time or Math.random in gameplay. Scenario construction awards no points/events.
- Preserve the mandatory tick order: pause, timers, motion/fall, pickups, deposit, safe zones, pulse, actors, theft then hits, spawn, outcome.
- Dash lasts 12 ticks; pulse push lasts 15; fall ignores invulnerability and waits 60 ticks before respawn.
- Store fuel in integer 1/60 units. Burn and drain in timer stage; extinguish before movement/interactions; test final-tick death before dawn survival.
- Only wander selects weak lights; drain follows its own 6m detection rule. Capacity counts actual lights and relights, never prelit scenario lamps.
- Keep evidence from actual commands in `docs/proof/phase-3`; never overwrite older phase tags/evidence. Document replaced tests in CHANGELOG.md; do not skip unchanged regression.
- GUI-only settings/audio/campaign need browser checks; a headless pass does not prove UI behavior or FPS.
- Use `.agents/skills/verify-game/SKILL.md` when collecting evidence.
