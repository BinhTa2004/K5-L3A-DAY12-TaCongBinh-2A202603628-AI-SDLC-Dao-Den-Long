# Đảo Đèn Lồng — Phase 1

- Read `docs/requirements/phase-1.txt` and `game.contract.json` before changing rules.
- `src/core.js` is the only gameplay implementation; browser and Python/QuickJS use it unchanged.
- Build: `python -m pip install -r requirements.txt`. Play: `python tools/serve.py`.
- Verify: `python tools/verify.py --phase phase-1`. Never claim success with a failing check.
- Run at fixed 60 Hz; distances use XZ, inclusive radius; snapshot zero precedes input.
- Never use wall time or Math.random in gameplay. Scenario construction awards no points/events.
- Keep evidence from actual commands in `docs/proof/phase-1`; identify unfinished work honestly.
- Use `.agents/skills/verify-game/SKILL.md` when collecting evidence.
