import json
from pathlib import Path
import subprocess
import sys
import unittest
from uuid import uuid4
from test_contract import ROOT, CONTRACT

sys.path.insert(0,str(ROOT/'tools'))
from leaderboard import Leaderboard
from bench import metrics


class PhaseFour(unittest.TestCase):
    def setUp(self):
        self.directory=ROOT/'artifacts'/('test-release-'+str(uuid4()))
        self.directory.mkdir(parents=True)

    def test_contract_and_measurement_commands(self):
        self.assertEqual(CONTRACT['contract_version'],'1.3')
        self.assertIn('tools/bench.py',CONTRACT['bench_cmd'])
        self.assertIn('tools/soak.py',CONTRACT['soak_cmd'])

    def test_real_frame_metric_definitions(self):
        m=metrics([10.0]*99+[1000.0])
        self.assertEqual(m['frames'],100)
        self.assertAlmostEqual(m['avg_fps'],100000/1990)
        self.assertEqual(m['p1_low_fps'],1)
        self.assertEqual(m['frame_ms_p95'],10)
        for data in [[],[0],[float('nan')]]:
            with self.assertRaises(ValueError):metrics(data)

    def test_benchmark_scene_exact_population_and_frozen_rules(self):
        import quickjs
        ctx=quickjs.Context()
        for f in ['src/core.js','src/benchmark.js']:ctx.eval((ROOT/f).read_text(encoding='utf-8'))
        ctx.eval('let game=LanternBench.create('+json.dumps(CONTRACT)+',42);')
        initial=ctx.eval('JSON.stringify(game.snapshot())')
        ctx.eval('for(let i=0;i<600;i++)LanternBench.step(game);')
        result=json.loads(ctx.eval('JSON.stringify(game.snapshot())'))
        self.assertEqual(len(result['shades']),200)
        self.assertEqual(len(result['motes']),100)
        self.assertTrue(all(s['state']=='wander' for s in result['shades']))
        self.assertEqual(result['player']['pos'],[0,0,0])
        self.assertEqual(result['player']['flames'],3)
        self.assertEqual(result['player']['carried'],0)
        self.assertEqual(result['time_left_s'],240)
        self.assertEqual([l['fuel'] for l in result['lanterns']],[100,100,100,0,0])
        self.assertNotEqual(json.loads(initial)['shades'][0]['pos'],result['shades'][0]['pos'])

    def test_benchmark_seed_is_repeatable(self):
        import quickjs
        c=quickjs.Context()
        for f in ['src/core.js','src/benchmark.js']:c.eval((ROOT/f).read_text(encoding='utf-8'))
        c.eval('let contract='+json.dumps(CONTRACT))
        a=c.eval('JSON.stringify(LanternBench.create(contract,42).snapshot())')
        self.assertEqual(a,c.eval('JSON.stringify(LanternBench.create(contract,42).snapshot())'))
        self.assertNotEqual(a,c.eval('JSON.stringify(LanternBench.create(contract,43).snapshot())'))

    def test_leaderboard_validation_persistence_and_export(self):
        store=Leaderboard(self.directory)
        for bad in ['ab','name with gap','x'*13,'Ánh']:
            with self.assertRaises(ValueError):store.add(dict(name=bad,score=100,nights_won=1,seed=7))
        for values in [dict(score=True,nights_won=1),dict(score=-1,nights_won=1),dict(score=2,nights_won=4)]:
            with self.assertRaises(ValueError):store.add(dict(name='May',seed=7,**values))
        store.add(dict(name='May_01',score=477,nights_won=1,seed=2026))
        reopened=Leaderboard(self.directory)
        self.assertEqual(reopened.read()[0]['name'],'May_01')
        self.assertRegex(reopened.read()[0]['achieved_at'],r'\+00:00$')
        target=self.directory/'out.json'
        p=subprocess.run([sys.executable,str(ROOT/'tools/serve.py'),'--data-dir',str(self.directory),'--export-leaderboard',str(target)],capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(target.read_text())['entries'],reopened.read())

    def test_leaderboard_top_ten_and_earlier_ties(self):
        store=Leaderboard(self.directory)
        for i in range(12):store.add(dict(name='May_'+str(i),score=i,nights_won=1,seed=i))
        self.assertEqual([e['score'] for e in store.read()],list(range(11,1,-1)))
        a=store.add(dict(name='First',score=1000,nights_won=2,seed=1))
        b=store.add(dict(name='Later',score=1000,nights_won=2,seed=2))
        self.assertEqual([e['name'] for e in b[:2]],['First','Later'])
        self.assertEqual(len(b),10)

    def test_duplicate_key_detection_and_legacy_aliases(self):
        import quickjs
        c=quickjs.Context();c.eval((ROOT/'web/accessibility.js').read_text(encoding='utf-8'))
        self.assertTrue(c.eval("!!LanternAccess.assign(LanternAccess.defaults,'jump','KeyW').error"))
        result=json.loads(c.eval("JSON.stringify(LanternAccess.assign(LanternAccess.defaults,'jump','KeyJ'))"))
        self.assertEqual(result['bindings']['jump'],'KeyJ')
        self.assertTrue(c.eval("LanternAccess.active(new Set(['ArrowUp']),'forward',LanternAccess.defaults)"))
        self.assertFalse(c.eval("LanternAccess.active(new Set(['ArrowUp']),'forward',{...LanternAccess.defaults,jump:'ArrowUp'})"))


if __name__=='__main__':unittest.main()
