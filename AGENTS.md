# Đảo Đèn Lồng — Phase 4 / v1.0.0

- Read `docs/requirements/phase-4.md`, `docs/adr/003-fuel-and-dawn.md`, and `game.contract.json` before changing rules. Contract1.3 preserves all Phase3 gameplay.
- `src/core.js` is the only gameplay implementation; browser and Python/QuickJS use it unchanged.
- Build: `python -m pip install -r requirements.txt`. Play: `python tools/serve.py`.
- Verify: `python tools/verify.py --phase phase-4`. Never claim success with a failing check.
- Run at fixed 60 Hz; distances use XZ, inclusive radius; snapshot zero precedes input.
- Never use wall time or Math.random in gameplay. Scenario construction awards no points/events.
- Preserve the mandatory tick order: pause, timers, motion/fall, pickups, deposit, safe zones, pulse, actors, theft then hits, spawn, outcome.
- Dash lasts 12 ticks; pulse push lasts 15; fall ignores invulnerability and waits 60 ticks before respawn.
- Store fuel in integer 1/60 units. Burn and drain in timer stage; extinguish before movement/interactions; test final-tick death before dawn survival.
- Only wander selects weak lights; drain follows its own 6m detection rule. Capacity counts actual lights and relights, never prelit scenario lamps.
- Benchmark: `python tools/bench.py --seed 42 --duration 30 --out bench.json`; soak: `python tools/soak.py --seed 7 --nights 10 --out soak.json`. Never substitute gameplay FPS for the standard200-shade benchmark or invent memory measurements.
- Benchmark uses the same batched renderer; its special scene disables input, gameplay timers, pickups, damage, spawning and outcomes. Creative-only entities/effects stay absent.
- Leaderboard lives on disk through tools/leaderboard.py; GUI and CLI export must read the same file. Do not commit player data or credentials.
- Keep evidence in `docs/proof/phase-4`; never overwrite older tags/evidence. UI minimum18px, large125%, persistent remapping and actual saved leaderboard require browser QA.
- GUI-only settings/audio/campaign need browser checks; a headless pass does not prove UI behavior or FPS.
- Use `.agents/skills/verify-game/SKILL.md` when collecting evidence.
