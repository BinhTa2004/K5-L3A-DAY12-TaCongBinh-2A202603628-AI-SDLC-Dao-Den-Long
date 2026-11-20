import json
import unittest
from test_contract import run, snaps, events, CONTRACT, T, ROOT


def lit(count, fuel=100):
    return [{'id': 'L'+str(i), 'lit': True, 'fuel': fuel} for i in range(1, count+1)]


class PhaseThree(unittest.TestCase):
    def test_version_and_standard_constants(self):
        self.assertEqual(CONTRACT['contract_version'], '1.3')  # Ticket-04 extends the unchanged fuel contract.
        for key, value in dict(fuel_max=100, fuel_decay_per_s=1, fuel_per_mote=10, relight_cost=5,
                               win_ratio=.6, drain_per_s=5, low_fuel_threshold=30, capacity_max=20).items():
            self.assertEqual(T[key], value)

    def test_scenario_defaults_and_no_reward(self):
        rows = run(0, scenario={'lanterns': [{'id': 'L1', 'lit': True}, {'id': 'L2', 'lit': False, 'fuel': 80, 'ever_lit': True}]})
        a, b = rows[0]['lanterns'][:2]
        self.assertEqual((a['fuel'], a['ever_lit'], a['relit_count']), (100, True, 0))
        self.assertEqual((b['fuel'], b['ever_lit']), (0, True))
        self.assertEqual(rows[0]['player']['capacity'], 10)
        self.assertEqual(rows[-1]['score'], 0)

    def test_exact_decay_and_extinction_reset(self):
        rows = run(60, scenario={'lanterns': [{'id': 'L1', 'lit': True, 'fuel': 1, 'deposited': 10}]})
        self.assertTrue(snaps(rows)[59]['lanterns'][0]['lit'])
        lamp = snaps(rows)[60]['lanterns'][0]
        self.assertEqual((lamp['lit'], lamp['fuel'], lamp['deposited'], lamp['ever_lit']), (False, 0, 0, True))
        self.assertEqual([e['tick'] for e in events(rows, 'lantern_out')], [60])

    def test_thousand_ticks_no_float_accumulation(self):
        rows = run(6000, scenario={'lanterns': lit(1)}, every=6000)
        self.assertEqual(events(rows, 'lantern_out')[0]['tick'], 6000)

    def test_refuel_ceil_clamp_and_points(self):
        rows = run(scenario={'player': {'carried': 10}, 'lanterns': [
            {'id': 'L1', 'pos': [0,0,0], 'lit': True, 'fuel': 75}]}, frames=[{'tick': 0, 'interact': True}])
        self.assertEqual(events(rows, 'refuel')[0]['data'], {'lantern_id': 'L1', 'amount': 3, 'fuel': 100})
        self.assertEqual(snaps(rows)[-1]['player']['carried'], 7)
        self.assertEqual(rows[-1]['score'], 15)
        self.assertEqual(events(rows, 'deposit'), [])
        self.assertEqual(events(rows, 'lantern_lit'), [])

    def test_full_lamp_is_ineligible_and_has_no_event(self):
        # Direct interaction before a tick isolates the exact-full state; during a tick decay runs first.
        import quickjs
        ctx = quickjs.Context()
        ctx.eval((ROOT/'src/core.js').read_text(encoding='utf-8'))
        scenario = {'random_motes': False, 'player': {'carried': 3}, 'lanterns': [{'id': 'L1', 'pos': [0,0,0], 'lit': True}]}
        result = ctx.eval('let g=new Lantern.Game('+json.dumps(CONTRACT)+',1,1,'+json.dumps(scenario)+');g.interactLantern();JSON.stringify({score:g.score,events:g.events,carried:g.player.carried})')
        self.assertEqual(json.loads(result), {'score': 0, 'events': [], 'carried': 3})

    def test_decay_before_refuel_makes_previous_full_receive_one(self):
        rows = run(scenario={'player': {'carried': 3}, 'lanterns': [{'id': 'L1', 'pos': [0,0,0], 'lit': True}]}, frames=[{'tick': 0, 'interact': True}])
        self.assertEqual(events(rows, 'refuel')[0]['data']['amount'], 1)

    def test_nearest_receiving_lamp_and_id_tie(self):
        rows = run(scenario={'player': {'carried': 4}, 'lanterns': [
            {'id': 'L1', 'pos': [1,0,0], 'lit': True, 'fuel': 50}, {'id': 'L2', 'pos': [-1,0,0]}]}, frames=[{'tick': 0, 'interact': True}])
        self.assertEqual(events(rows, 'refuel')[0]['data']['lantern_id'], 'L1')

    def test_first_light_and_relight_capacity_and_scores(self):
        for ever, cost, bonus in [(False, 10, 100), (True, 5, 40)]:
            with self.subTest(ever=ever):
                rows = run(scenario={'player': {'carried': cost}, 'lanterns': [
                    {'id': 'L1', 'pos': [0,0,0], 'ever_lit': ever}]}, frames=[{'tick': 0, 'interact': True}])
                lamp = snaps(rows)[-1]['lanterns'][0]
                self.assertEqual((lamp['lit'], lamp['fuel'], lamp['ever_lit'], lamp['relit_count']), (True, 100, True, int(ever)))
                self.assertEqual(events(rows, 'lantern_lit')[0]['data']['relight'], ever)
                self.assertEqual(rows[-1]['score'], cost*5+bonus)
                self.assertEqual(snaps(rows)[-1]['player']['capacity'], 12)

    def test_relight_remembers_partial_deposits(self):
        rows = run(scenario={'player': {'carried': 2}, 'lanterns': [
            {'id': 'L1', 'pos': [0,0,0], 'ever_lit': True, 'deposited': 3}]}, frames=[{'tick': 0, 'interact': True}])
        self.assertTrue(snaps(rows)[-1]['lanterns'][0]['lit'])
        self.assertEqual(rows[-1]['score'], 50)

    def test_capacity_scenario_cap_reset_and_pickup(self):
        for successes, capacity in [(0,10),(2,14),(5,20),(100,20)]:
            rows = run(scenario={'player': {'successful_lights': successes}, 'motes': [[0,0,0]]*25})
            self.assertEqual(snaps(rows)[-1]['player']['capacity'], capacity)
            self.assertEqual(snaps(rows)[-1]['player']['carried'], capacity)
        self.assertEqual(snaps(run(night=2))[0]['player']['capacity'], 10)

    def test_full_set_of_lights_never_wins_early(self):
        rows = run(120, scenario={'lanterns': lit(5)})
        self.assertEqual(rows[-1]['state'], 'playing')
        self.assertEqual(rows[-1]['ticks'], 120)
        self.assertEqual(events(rows, 'game_over'), [])

    def test_dawn_thresholds_for_every_night(self):
        for night, needed in [(1,3),(2,4),(3,5)]:
            for count, result in [(needed-1,'lost'),(needed,'won')]:
                with self.subTest(night=night,count=count):
                    rows = run(3, night=night, scenario={'lanterns': lit(count), 'time_left_s': 1/60})
                    self.assertEqual(rows[-1]['state'], result)
                    self.assertEqual(events(rows,'game_over')[0]['data']['reason'], 'dawn_survived' if result=='won' else 'dawn')
                    self.assertEqual(rows[-1]['ticks'], 1)

    def test_last_tick_oil_extinction_counts_before_outcome(self):
        lamps = lit(3); lamps[0]['fuel'] = 1/60
        rows = run(scenario={'lanterns': lamps, 'time_left_s': 1/60})
        self.assertEqual(rows[-1]['state'], 'lost')
        self.assertEqual(events(rows,'game_over')[0]['data']['reason'], 'dawn')

    def test_last_tick_death_overrides_survival(self):
        rows = run(scenario={'player': {'flames': 1}, 'shades': [{'pos': [0,0,0]}],
            'lanterns': lit(3), 'time_left_s': 1/60})
        self.assertEqual(events(rows,'game_over')[0]['data']['reason'], 'no_flames')

    def test_final_tick_relight_can_rescue_dawn(self):
        lamps = lit(2)+[{'id': 'L3', 'pos': [0,0,0], 'ever_lit': True}]
        rows = run(scenario={'player': {'carried': 5}, 'lanterns': lamps, 'time_left_s': 1/60}, frames=[{'tick': 0, 'interact': True}])
        self.assertEqual(rows[-1]['state'], 'won')
        self.assertEqual(events(rows,'game_over')[0]['data']['reason'], 'dawn_survived')

    def test_dawn_score_uses_floor_of_unrounded_oil(self):
        rows = run(scenario={'lanterns': lit(3,60), 'time_left_s': 1/60})
        # Output rounds59.983 to60.0, but reward uses floor59, not rounded60.
        self.assertEqual(snaps(rows)[-1]['lanterns'][0]['fuel'], 60)
        self.assertEqual(rows[-1]['score'], 3*(50+59)+3*50)

    def test_pause_freezes_oil_and_drain_counters(self):
        scenario = {'player': {'pos': [30,0,0]}, 'lanterns': [{'id':'L1','pos':[0,0,0],'lit':True,'fuel':20}],
            'shades':[{'id':'S1','pos':[1,0,0],'state':'drain','target_lantern_id':'L1'}]}
        rows = run(100, scenario=scenario, frames=[{'tick':0,'pause':True}])
        self.assertEqual(snaps(rows)[-1]['lanterns'][0]['fuel'], 20)
        self.assertEqual(events(rows,'fuel_drain'), [])

    def test_single_and_stacked_drain_fixed_rate_and_events(self):
        for count in [1,2]:
            scenario = {'player': {'pos': [30,0,0]}, 'lanterns': [{'id':'L1','pos':[0,0,0],'lit':True,'fuel':20}],
                'shades':[{'id':'S'+str(i+1),'pos':[1,0,0],'state':'drain','target_lantern_id':'L1'} for i in range(count)]}
            rows = run(60, scenario=scenario)
            self.assertEqual(snaps(rows)[-1]['lanterns'][0]['fuel'], 20-1-5*count)
            self.assertEqual(len(events(rows,'fuel_drain')), count)
            self.assertEqual({e['tick'] for e in events(rows,'fuel_drain')}, {60})

    def test_only_wander_targets_weak_lights_and_tie(self):
        lamps = [{'id':'L1','pos':[1,0,0],'lit':True,'fuel':20},{'id':'L2','pos':[-1,0,0],'lit':True,'fuel':20}]
        rows = run(scenario={'player': {'pos':[30,0,0]}, 'lanterns':lamps,
            'shades':[{'id':'S1','pos':[0,0,0],'state':'wander'}]})
        self.assertEqual(snaps(rows)[-1]['shades'][0]['state'], 'drain')
        tied = run(61,scenario={'player':{'pos':[30,0,0]},'lanterns':lamps,'shades':[{'id':'S1','pos':[0,0,0],'state':'wander'}]})
        self.assertEqual(events(tied,'fuel_drain')[0]['data']['lantern_id'],'L1')
        self.assertEqual(snaps(tied)[-1]['lanterns'][0]['fuel'],14)
        self.assertEqual(snaps(tied)[-1]['lanterns'][1]['fuel'],19)
        rows = run(scenario={'player':{'pos':[10,0,0]},'lanterns':lamps,
            'shades':[{'id':'S1','pos':[0,0,0],'state':'chase'}]})
        self.assertEqual(snaps(rows)[-1]['shades'][0]['state'], 'chase')

    def test_weak_lamp_loses_safe_zone_but_exact_thirty_keeps_it(self):
        # 30+1/60 becomes exactly30 during step2; next step becomes weak.
        scenario = {'lanterns':[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':30+1/60}],
            'shades':[{'id':'S1','pos':[6.02,0,0],'state':'chase'}]}
        rows = run(2,scenario=scenario)
        self.assertEqual(snaps(rows)[1]['shades'][0]['pos'][0], 6)
        self.assertLess(snaps(rows)[2]['shades'][0]['pos'][0], 6)

    def test_drainer_switches_to_chase_at_six_metres(self):
        rows = run(scenario={'player':{'pos':[6,0,0]},'lanterns':[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':20}],
            'shades':[{'pos':[0,0,0],'state':'drain','target_lantern_id':'L1'}]})
        self.assertEqual(snaps(rows)[-1]['shades'][0]['state'], 'chase')

    def test_refuel_restores_safe_zone_ejects_and_stops_drain(self):
        scenario = {'player':{'pos':[0,0,0],'carried':2},'lanterns':[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':20}],
            'shades':[{'pos':[1,0,0],'state':'drain','target_lantern_id':'L1'}]}
        rows = run(30,scenario=scenario,frames=[{'tick':0,'interact':True}])
        self.assertEqual(events(rows,'player_hit'), [])
        self.assertEqual(snaps(rows)[30]['shades'][0]['pos'][0], 6)
        self.assertGreater(snaps(rows)[30]['lanterns'][0]['fuel'], 30)
        self.assertEqual(events(rows,'fuel_drain'), [])

    def test_draining_pulse_reward_is_total_fifteen(self):
        rows = run(scenario={'player':{'carried':3},'lanterns':[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':20}],
            'shades':[{'pos':[1,.8,0],'state':'drain','target_lantern_id':'L1'}]},frames=[{'tick':0,'pulse':True}])
        self.assertEqual(rows[-1]['score'], 15)
        self.assertEqual(snaps(rows)[-1]['shades'][0]['state'], 'stunned')

    def test_invalid_new_scenario_fields_are_rejected(self):
        for scenario in [{'player':{'successful_lights':-1}}, {'lanterns':[{'id':'L1','fuel':101}]},
            {'lanterns':[{'id':'L1','ever_lit':1}]}, {'shades':[{'pos':[0,0,0],'target_lantern_id':'L9'}]}]:
            with self.subTest(scenario=scenario), self.assertRaises(Exception):
                run(scenario=scenario)

    def test_stun_expiry_returns_to_wander_before_reselecting(self):
        rows = run(2,scenario={'player':{'pos':[30,0,0]},'lanterns':[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':20}],
            'shades':[{'id':'S1','pos':[1,0,0],'state':'stunned','state_ticks_left':1,'target_lantern_id':'L1'}]})
        self.assertEqual(snaps(rows)[1]['shades'][0]['state'],'wander')
        self.assertEqual(snaps(rows)[2]['shades'][0]['state'],'drain')

    def test_drain_exits_when_lamp_is_out_or_out_of_range(self):
        for lamp, pos in [({'id':'L1','pos':[0,0,0],'lit':False},[1,0,0]),
                          ({'id':'L1','pos':[0,0,0],'lit':True,'fuel':20},[3,0,0])]:
            rows=run(scenario={'player':{'pos':[30,0,0]},'lanterns':[lamp],
                'shades':[{'pos':pos,'state':'drain','target_lantern_id':'L1'}]})
            self.assertEqual(snaps(rows)[-1]['shades'][0]['state'],'wander')


if __name__ == '__main__':
    unittest.main()
