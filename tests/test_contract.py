import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from headless import simulate

CONTRACT = json.loads((ROOT / 'game.contract.json').read_text())
T = CONTRACT['tuning']


def run(ticks=1, scenario=None, frames=None, night=1, every=1, seed=42):
    base = {'random_motes': False, 'random_shades': False, 'motes': [], 'shades': []}
    base.update(scenario or {})
    return [json.loads(s) for s in simulate(dict(contract=CONTRACT, seed=seed, night=night,
        ticks=ticks, snapshotEvery=every, scenario=base, inputs={'frames': frames or []})).splitlines()]


def snaps(rows):
    return [r for r in rows if r['type'] == 'snapshot']


def events(rows, name):
    return [r for r in rows if r.get('name') == name]


class PhaseOne(unittest.TestCase):
    def test_tick_zero_and_exact_steps(self):
        rows = run(60, frames=[{'tick': 0, 'move': [0, 1]}])
        self.assertEqual(snaps(rows)[0]['player']['pos'], [0, 0, 0])
        self.assertAlmostEqual(snaps(rows)[-1]['player']['pos'][2], T['player_speed'], places=3)
        self.assertEqual(rows[-1]['ticks'], 60)
        self.assertEqual(snaps(rows)[-1]['time_left_s'], T['night1_duration_s'] - 1)

    def test_camera_diagonal_and_persistent_fields(self):
        rows = run(60, frames=[{'tick': 0, 'move': [1, 1], 'cam_yaw_deg': 90}, {'tick': 30, 'interact': True}])
        p = snaps(rows)[-1]['player']['pos']
        self.assertAlmostEqual(p[0], T['player_speed'] / 2**.5, places=3)
        self.assertAlmostEqual(p[2], -T['player_speed'] / 2**.5, places=3)

    def test_inclusive_pickup_and_capacity(self):
        rows = run(1, scenario={'motes': [[T['pickup_radius'], 0, 0]] * 12})
        self.assertEqual(snaps(rows)[-1]['player']['carried'], T['carry_capacity'])
        self.assertEqual(len(events(rows, 'mote_picked')), T['carry_capacity'])

    def test_partial_deposits_and_button_edge(self):
        rows = run(3, scenario={'player': {'carried': 4}, 'lanterns': [{'id': 'L1', 'pos': [0, 0, 0]}]},
                   frames=[{'tick': 0, 'interact': True}])
        self.assertEqual(len(events(rows, 'deposit')), 1)
        self.assertEqual(snaps(rows)[-1]['lanterns'][0]['deposited'], 4)
        self.assertEqual(rows[-1]['score'], 4 * T['score']['per_mote'])

    def test_lighting_and_winning(self):
        lanterns = [{'id': 'L1', 'pos': [0, 0, 0]}] + [{'id': 'L'+str(i), 'lit': True} for i in range(2, 6)]
        rows = run(20, scenario={'player': {'carried': 10}, 'lanterns': lanterns}, frames=[{'tick': 0, 'interact': True}])
        self.assertEqual(rows[-1]['state'], 'won')
        self.assertEqual(rows[-1]['ticks'], 1)
        self.assertEqual(events(rows, 'game_over')[0]['data']['reason'], 'all_lit')
        self.assertEqual(events(rows, 'lantern_lit')[0]['tick'], 1)

    def test_scenario_has_no_rewards_or_events(self):
        rows = run(0, scenario={'lanterns': [{'id': 'L1', 'lit': True}]})
        self.assertEqual(rows[-1]['score'], 0)
        self.assertEqual(len([r for r in rows if r['type'] == 'event' and r['name'] != 'night_start']), 0)

    def test_pulse_cost_stun_and_no_held_repeat(self):
        rows = run(2, scenario={'player': {'carried': 10}, 'shades': [{'id': 'S1', 'pos': [2, 0, 0]}]}, frames=[{'tick': 0, 'pulse': True}])
        self.assertEqual(len(events(rows, 'pulse')), 1)
        self.assertEqual(snaps(rows)[-1]['player']['carried'], 10 - T['pulse_cost'])
        self.assertEqual(snaps(rows)[-1]['shades'][0]['state'], 'stunned')
        self.assertEqual(rows[-1]['score'], T['score']['per_stun'])

    def test_no_pulse_without_light(self):
        self.assertEqual(events(run(frames=[{'tick': 0, 'pulse': True}]), 'pulse'), [])

    def test_damage_invulnerability_and_loss(self):
        rows = run(3, scenario={'player': {'flames': 1, 'carried': 8}, 'shades': [{'pos': [0, 0, 0]}]})
        self.assertEqual(rows[-1]['state'], 'lost')
        self.assertEqual(len(events(rows, 'player_hit')), 1)
        self.assertEqual(events(rows, 'player_hit')[0]['data']['dropped'], 4)
        self.assertEqual(events(rows, 'game_over')[0]['data']['reason'], 'no_flames')

    def test_dawn(self):
        rows = run(30, scenario={'time_left_s': 1 / 60})
        self.assertEqual(rows[-1]['ticks'], 1)
        self.assertEqual(events(rows, 'game_over')[0]['data']['reason'], 'dawn')

    def test_jump_returns_to_ground(self):
        rows = run(90, frames=[{'tick': 0, 'jump': True}])
        self.assertGreater(snaps(rows)[10]['player']['pos'][1], 0)
        self.assertEqual(snaps(rows)[-1]['player']['pos'][1], 0)

    def test_deterministic_with_random_spawning(self):
        opts = dict(contract=CONTRACT, seed=987, night=1, ticks=1600, snapshotEvery=10, scenario={}, inputs={})
        self.assertEqual(simulate(opts), simulate(opts))

    def test_malformed_inputs_and_scenarios(self):
        for frames in [[{'tick': 0}, {'tick': 0}], [{'tick': -1}], [{'tick': 2}, {'tick': 1}], [{'tick': 0, 'move': [2, 0]}], [{'tick': 0, 'pulse': 1}]]:
            with self.subTest(frames=frames), self.assertRaises(Exception):
                run(frames=frames)
        for scenario in [{'motes': 'wrong'}, {'player': {'pos': [0, 0]}}, {'random_motes': 0}, {'lanterns': [{'id': 'L6'}]}]:
            with self.subTest(scenario=scenario), self.assertRaises(Exception):
                run(scenario=scenario)

    def test_cli_error_exit_code(self):
        import uuid
        scratch = ROOT / 'artifacts'
        scratch.mkdir(exist_ok=True)
        source = scratch / ('bad-' + str(uuid.uuid4()) + '.json')
        output = source.with_suffix('.jsonl')
        try:
            source.write_text('{"frames":[{"tick":0},{"tick":0}]}')
            p = subprocess.run([sys.executable, str(ROOT/'tools/headless.py'), '--seed', '1', '--night', '1', '--ticks', '1', '--inputs', str(source), '--out', str(output)], capture_output=True)
            self.assertEqual(p.returncode, 2)
            self.assertIn(b'ContractError', p.stderr)
        finally:
            source.unlink(missing_ok=True)
            output.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
