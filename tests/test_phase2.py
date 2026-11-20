import json
import math
import unittest
from test_contract import run, snaps, events, CONTRACT, T


class PhaseTwo(unittest.TestCase):
    def test_standard_tuning(self):
        expected = dict(player_speed=6, carry_capacity=10, lantern_cost=10, pickup_radius=1,
                        interact_radius=2, pulse_cost=3, pulse_radius=5, flames=3, invuln_s=1.5,
                        hit_drop_ratio=.5, pulse_stun_s=2, pulse_push_m=4, pulse_cooldown_s=3,
                        safe_radius=6, shade_speed=4, shade_hit_radius=1, dash_speed=14,
                        dash_duration_s=.2, dash_cooldown_s=1.5, night1_duration_s=240,
                        night2_duration_s=270, night3_duration_s=300)  # Ticket-03 replaces durations only.
        for k, v in expected.items():
            self.assertEqual(T[k], v, k)

    def test_dash_exact_distance_duration_and_cooldown(self):
        rows = run(13, frames=[{'tick': 0, 'dash': True}])
        states = snaps(rows)
        self.assertEqual(len(events(rows, 'dash')), 1)
        self.assertAlmostEqual(states[12]['player']['pos'][2], 2.8)
        self.assertEqual(states[13]['player']['pos'][2], 2.8)
        self.assertEqual(states[1]['player']['dash_cd_s'], 1.5)
        self.assertEqual(states[13]['player']['dash_cd_s'], 1.3)
        # Starting at 0, a fresh edge at input tick 90 is accepted.
        rows = run(91, frames=[{'tick': 0, 'dash': True}, {'tick': 1, 'dash': False}, {'tick': 2, 'dash': True}, {'tick': 89, 'dash': False}, {'tick': 90, 'dash': True}])
        self.assertEqual([e['tick'] for e in events(rows, 'dash')], [1, 91])

    def test_air_dash_locks_height_without_invulnerability(self):
        rows = run(12, scenario={'player': {'pos': [0, 2, 0]}}, frames=[{'tick': 0, 'dash': True}])
        self.assertTrue(all(s['player']['pos'][1] == 2 for s in snaps(rows)))
        self.assertFalse(snaps(rows)[-1]['player']['invuln'])

    def test_jump_analytic_height_and_air_control(self):
        rows = run(6, frames=[{'tick': 0, 'jump': True, 'move': [1, 0]}])
        self.assertEqual(snaps(rows)[-1]['player']['pos'], [.6, .6, 0])

    def test_pickup_height_and_inclusive_distance(self):
        rows = run(scenario={'motes': [[1, 1.5, 0], [0, 1.501, 0], [1.001, 0, 0]]})
        self.assertEqual(snaps(rows)[-1]['player']['carried'], 1)

    def test_initial_motes_unique_spawn_schedule_and_cap(self):
        rows = run(240, scenario={'random_motes': True}, every=240)
        # Explicit [] replaces initial list; default initial map has exactly 20.
        from headless import simulate
        initial = json.loads(simulate(dict(contract=CONTRACT, seed=1, night=1, ticks=0, snapshotEvery=1, scenario={}, inputs={})).splitlines()[0])
        self.assertEqual(initial['motes_active'], 20)
        self.assertEqual(len({tuple(m['pos']) for m in initial['motes']}), 20)
        self.assertEqual(snaps(rows)[-1]['motes_active'], 1)
        rows = run(240*50, scenario={'random_motes': True}, every=12000)
        self.assertEqual(snaps(rows)[-1]['motes_active'], 24)  # all Night 1 points occupied

    def test_nearest_unlit_lantern_and_tie(self):
        rows = run(scenario={'player': {'carried': 10}, 'lanterns': [
            {'id': 'L1', 'pos': [2, 0, 0], 'lit': True}, {'id': 'L2', 'pos': [1, 0, 0]}, {'id': 'L3', 'pos': [-1, 0, 0]}]}, frames=[{'tick': 0, 'interact': True}])
        self.assertEqual(events(rows, 'deposit')[0]['data']['lantern_id'], 'L2')

    def test_pulse_is_3d_targets_locked_and_pushes_over_15_ticks(self):
        scenario = {'player': {'carried': 10}, 'shades': [
            {'id': 'S1', 'pos': [0, .8, 0]}, {'id': 'S2', 'pos': [0, 5.801, 0]}, {'id': 'S3', 'pos': [5, .8, 0]}]}
        rows = run(15, scenario=scenario, frames=[{'tick': 0, 'pulse': True}])
        self.assertEqual(events(rows, 'pulse')[0]['data']['stunned_ids'], ['S1', 'S3'])
        self.assertEqual(snaps(rows)[1]['shades'][0]['pos'][0], .267)
        self.assertEqual(snaps(rows)[-1]['shades'][0]['pos'][0], 4)
        self.assertEqual(rows[-1]['score'], 10)

    def test_hit_drop_ring_ttl_recoil_and_one_hit(self):
        rows = run(2, scenario={'player': {'carried': 9}, 'shades': [
            {'id': 'S2', 'pos': [0, 0, 0]}, {'id': 'S1', 'pos': [0, 0, 0]}]})
        self.assertEqual(len(events(rows, 'player_hit')), 1)
        s = snaps(rows)[1]
        self.assertEqual(s['player']['carried'], 5)
        self.assertEqual(s['player']['flames'], 2)
        self.assertTrue(s['player']['invuln'])
        self.assertEqual(next(x for x in s['shades'] if x['id'] == 'S1')['state'], 'recoil')
        for m in s['motes']:
            self.assertTrue(1.499 <= math.hypot(m['pos'][0], m['pos'][2]) <= 2.501)
            self.assertEqual(m['ttl_s'], 8)

    def test_fall_ignores_invulnerability_once_and_respawns(self):
        rows = run(61, scenario={'player': {'pos': [50, -10.1, 0], 'carried': 7, 'invuln_ticks': 999}}, frames=[{'tick': 0, 'move': [0,1]}])
        hits = events(rows, 'player_hit')
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]['data'], {'by': 'fall', 'flames': 2, 'dropped': 0, 'lost': 7})
        self.assertEqual(snaps(rows)[60]['player']['pos'][0], 50)
        self.assertEqual(snaps(rows)[61]['player']['pos'], [0, 0, 0])
        self.assertEqual(snaps(rows)[61]['player']['vel'], [0, 0, 0])
        self.assertTrue(snaps(rows)[61]['player']['invuln'])

    def test_death_priority_and_win_at_dawn(self):
        lanterns = [{'id': 'L'+str(i), 'lit': True} for i in range(1, 6)]
        self.assertEqual(events(run(scenario={'lanterns': lanterns, 'player': {'flames': 0}}), 'game_over')[0]['data']['reason'], 'no_flames')
        self.assertEqual(events(run(scenario={'lanterns': lanterns, 'time_left_s': 1/60}), 'game_over')[0]['data']['reason'], 'dawn_survived')

    def test_pause_freezes_counters_ttl_and_spawn(self):
        rows = run(241, scenario={'random_motes': True, 'player': {'invuln_ticks': 10, 'pulse_cd_ticks': 20},
                   'motes': [{'pos': [10, 0, 0], 'kind': 'dropped', 'ttl_ticks': 480}]},
                   frames=[{'tick': 0, 'pause': True}, {'tick': 1, 'pause': False}, {'tick': 239, 'pause': True}])
        s = snaps(rows)
        self.assertEqual(s[239]['sim_tick'], 0)
        self.assertEqual(s[239]['state'], 'paused')
        self.assertEqual(s[239]['motes'][0]['ttl_s'], 8)
        self.assertEqual(s[239]['player']['pulse_cd_s'], .333)
        self.assertEqual(s[240]['sim_tick'], 1)
        self.assertEqual(len(events(rows, 'paused')), 1)
        self.assertEqual(len(events(rows, 'resumed')), 1)

    def test_shade_spawns_at_exact_ticks(self):
        rows = run(780, scenario={'random_shades': True, 'player': {'invuln_ticks': 10000}})
        self.assertEqual([e['tick'] for e in events(rows, 'shade_spawned')], [300, 300, 780])
        self.assertEqual(snaps(rows)[300]['shades'][0]['state'], 'spawning')

    def test_safe_zone_ejection_and_boundary(self):
        rows = run(60, scenario={'lanterns': [{'id': 'L1', 'pos': [0, 0, 0], 'lit': True}],
            'shades': [{'pos': [1, 0, 0]}]})
        self.assertEqual(events(rows, 'player_hit'), [])
        self.assertEqual(snaps(rows)[30]['shades'][0]['pos'][0], 6)
        self.assertGreaterEqual(snaps(rows)[-1]['shades'][0]['pos'][0], 6)

    def test_charm_pickup_speed_expiry_respawn(self):
        rows = run(60, night=2, scenario={'player': {'pos': [35, 0, 0]}}, frames=[{'tick': 1, 'move': [1, 0]}])
        self.assertEqual(events(rows, 'charm_picked')[0]['data'], {'charm_id': 'C1', 'charm_ticks': 600})
        self.assertAlmostEqual(snaps(rows)[60]['player']['pos'][0], 35 + 59*.12, places=3)
        self.assertFalse(snaps(rows)[1]['charms'][0]['available'])
        self.assertEqual(snaps(rows)[1]['charms'][0]['respawn_s'], 45)
        rows = run(2, night=2, scenario={'charms': [{'id': 'C1', 'pos': [10, 0, 0], 'available': False, 'respawn_ticks': 2}]})
        self.assertTrue(snaps(rows)[2]['charms'][0]['available'])

    def test_charm_dash_repress_ignores_active_dash(self):
        rows = run(14, scenario={'player': {'charm_ticks': 600}}, frames=[{'tick': 0, 'dash': True},
            {'tick': 1, 'dash': False}, {'tick': 2, 'dash': True}, {'tick': 12, 'dash': False}, {'tick': 13, 'dash': True}])
        self.assertEqual([e['tick'] for e in events(rows, 'dash')], [1, 14])

    def test_drifter_steals_before_shade_even_while_invulnerable(self):
        rows = run(night=2, scenario={'player': {'carried': 10},
            'drifters': [{'id': 'D1', 'pos': [0, 0, 0], 'state': 'chase'}], 'shades': [{'pos': [0, 0, 0]}]})
        self.assertEqual(events(rows, 'drifter_steal')[0]['data']['carried'], 7)
        self.assertEqual(events(rows, 'player_hit')[0]['data']['dropped'], 3)
        rows = run(night=2, scenario={'player': {'carried': 5, 'invuln_ticks': 100}, 'drifters': [{'pos': [0, 0, 0]}]})
        self.assertEqual(len(events(rows, 'drifter_steal')), 1)
        self.assertEqual(snaps(rows)[-1]['player']['flames'], 3)

    def test_drifter_pulse_flee_drop_and_removal(self):
        rows = run(night=2, scenario={'player': {'carried': 10}, 'drifters': [{'id': 'D1', 'pos': [2, 0, 0], 'state': 'chase'}]}, frames=[{'tick': 0, 'pulse': True}])
        self.assertEqual(snaps(rows)[-1]['drifters'][0]['state'], 'flee')
        self.assertEqual(events(rows, 'drifter_steal'), [])
        rows = run(121, night=2, scenario={'player': {'carried': 10}, 'drifters': [
            {'id': 'D1', 'pos': [2, 0, 0], 'state': 'flee', 'stolen': 3, 'state_ticks_left': 240}]}, frames=[{'tick': 0, 'pulse': True}])
        self.assertEqual(events(rows, 'drifter_drop')[0]['data']['amount'], 3)
        self.assertEqual(snaps(rows)[1]['motes_active'], 3)
        self.assertEqual(snaps(rows)[121]['drifters'], [])

    def test_night_two_bridge_and_falling_off_side(self):
        rows = run(60, night=2, scenario={'player': {'pos': [30, 0, 0]}, 'charms': []}, frames=[{'tick': 0, 'move': [1, 0]}])
        self.assertEqual(snaps(rows)[-1]['player']['pos'], [36, 0, 0])
        rows = run(120, night=2, scenario={'player': {'pos': [35, 0, 0]}}, frames=[{'tick': 0, 'move': [0, 1]}])
        self.assertEqual(len(events(rows, 'player_hit')), 1)

    def test_launch_pad_lands_on_other_island_and_ignores_input(self):
        rows = run(84, night=2, scenario={'player': {'pos': [20, 0, 18]}}, frames=[{'tick': 0, 'move': [-1, 0]}])
        p = snaps(rows)[-1]['player']
        self.assertGreater(p['pos'][0], 45)
        self.assertLess(math.hypot(p['pos'][0]-70, p['pos'][2]), 28)
        self.assertEqual(p['pos'][1], 0)

    def test_night_three_ramp_wall_pad_and_tower(self):
        a = math.pi/6
        start = [30*math.cos(a), 0, 30*math.sin(a)]
        rows = run(61, night=3, scenario={'player': {'pos': start}, 'wind_enabled': False}, frames=[{'tick': 0, 'move': [-math.cos(a), -math.sin(a)]}])
        self.assertAlmostEqual(snaps(rows)[60]['player']['pos'][1], 3, places=2)
        rows = run(60, night=3, scenario={'player': {'pos': [0, 0, 25]}}, frames=[{'tick': 0, 'move': [0, -1]}])
        self.assertGreaterEqual(snaps(rows)[-1]['player']['pos'][2], 24)
        rows = run(90, night=3, scenario={'player': {'pos': [0, 3, 13]}, 'wind_enabled': False})
        self.assertTrue(any(s['player']['pos'][1] >= 6 and s['player']['grounded'] for s in snaps(rows)))
        rows = run(60, night=3, scenario={'player': {'pos': [0, 6, 6]}, 'wind_enabled': False}, frames=[{'tick': 0, 'move': [0, -1]}])
        self.assertGreaterEqual(snaps(rows)[-1]['player']['pos'][2], 2)

    def test_wind_schedule_and_disable(self):
        rows = run(2100, night=3, scenario={'wind_enabled': True, 'player': {'pos': [0, 0, 30], 'invuln_ticks': 10000}})
        s = snaps(rows)
        self.assertFalse(s[1799]['wind']['active'])
        self.assertTrue(s[1800]['wind']['active'])
        self.assertFalse(s[2100]['wind']['active'])
        self.assertNotEqual(s[1799]['player']['pos'], s[1900]['player']['pos'])
        rows = run(1850, night=3, scenario={'wind_enabled': False})
        self.assertFalse(snaps(rows)[-1]['wind']['active'])

    def test_three_maps_contract_shape_and_night_start(self):
        for night, count in [(1, 5), (2, 6), (3, 7)]:
            rows = run(0, night=night)
            s = rows[0]
            self.assertEqual(s['night'], night)
            self.assertEqual(len(s['lanterns']), count)
            self.assertEqual(events(rows, 'night_start')[0]['data'], {'night': night})
            for key in ['vel', 'grounded', 'invuln', 'dash_cd_s', 'pulse_cd_s', 'charm_s']:
                self.assertIn(key, s['player'])
            for key in ['motes', 'drifters', 'charms', 'wind']:
                self.assertIn(key, s)

    def test_recoil_exactly_two_metres_in_sixty_steps(self):
        rows = run(61, scenario={'shades': [{'pos': [0,0,0]}]})
        self.assertEqual(snaps(rows)[61]['shades'][0]['pos'][0], 2)

    def test_charm_expiry_before_motion_and_dropped_ttl(self):
        rows = run(2, scenario={'player': {'charm_ticks': 2}, 'motes': [
            {'pos': [10,0,0], 'kind': 'dropped', 'ttl_ticks': 2}]}, frames=[{'tick': 0, 'move': [0,1]}])
        self.assertEqual(snaps(rows)[1]['player']['pos'][2], .12)
        self.assertEqual(snaps(rows)[2]['player']['pos'][2], .22)
        self.assertEqual(snaps(rows)[2]['motes'], [])

    def test_pickup_then_deposit_then_pulse_order(self):
        rows = run(scenario={'player': {'carried': 2}, 'motes': [[0,0,0]]}, frames=[{'tick': 0, 'pulse': True}])
        self.assertEqual(len(events(rows, 'pulse')), 1)
        self.assertEqual(snaps(rows)[-1]['player']['carried'], 0)
        rows = run(scenario={'player': {'carried': 10}, 'lanterns': [{'id': 'L1', 'pos': [0,0,0]}]},
                   frames=[{'tick': 0, 'pulse': True, 'interact': True}])
        self.assertEqual(events(rows, 'pulse'), [])
        self.assertEqual(rows[-1]['score'], 150)  # Ticket-03: 10*5 + first-light 100.

    def test_spawn_drifter_schedule_and_cap(self):
        rows = run(3600, night=2, scenario={'random_drifters': True}, every=1200)
        s = snaps(rows)
        self.assertEqual([len(x['drifters']) for x in s], [0,1,2,2])
        self.assertEqual([d['id'] for d in s[-1]['drifters']], ['D1','D2'])

    def test_detection_hysteresis_and_collision_height(self):
        rows = run(scenario={'shades': [{'id': 'S1', 'pos': [13,0,0], 'state': 'wander'},
             {'id': 'S2', 'pos': [19,0,0], 'state': 'chase'}, {'id': 'S3', 'pos': [0,2,0]}]})
        self.assertEqual(snaps(rows)[-1]['shades'][0]['state'], 'wander')
        self.assertEqual(snaps(rows)[-1]['shades'][1]['state'], 'wander')
        self.assertEqual(events(rows, 'player_hit'), [])

    def test_pulse_refreshes_stunned_target(self):
        rows = run(120, scenario={'player': {'carried': 3}, 'shades': [
            {'id': 'S1', 'pos': [1,.8,0], 'state': 'stunned', 'state_ticks_left': 2}]}, frames=[{'tick': 0, 'pulse': True}])
        self.assertEqual(snaps(rows)[120]['shades'][0]['state'], 'stunned')
        self.assertEqual(rows[-1]['score'], 5)


if __name__ == '__main__':
    unittest.main()
