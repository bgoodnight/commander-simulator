import unittest,subprocess,sys,json,tempfile
from pathlib import Path
from commander_sim import ServiceRegistry,ServiceConfigurationError
from commander_sim.legacy import run

class ServiceTests(unittest.TestCase):
 def test_order_and_injected_dependencies(self):
  r=ServiceRegistry();r.register('stack',lambda d:('stack',d['zones']),dependencies=('zones',));r.register('zones',lambda d:[])
  a=r.build();self.assertIs(a['stack'][1],a['zones'])
 def test_each_build_has_independent_state(self):
  r=ServiceRegistry();r.register('zones',lambda d:[]);a=r.build();b=r.build();a['zones'].append(1);self.assertEqual(b['zones'],[])
 def test_independent_registries(self):
  a=ServiceRegistry();b=ServiceRegistry();a.register('game',lambda d:'a');b.register('game',lambda d:'b')
  self.assertEqual((a.build()['game'],b.build()['game']),('a','b'))
 def test_duplicate_rejected(self):
  r=ServiceRegistry();r.register('x',lambda d:0)
  with self.assertRaises(ServiceConfigurationError):r.register('x',lambda d:1)
 def test_unknown_dependency_fails_before_factories(self):
  called=[];r=ServiceRegistry();r.register('good',lambda d:called.append(1));r.register('bad',lambda d:0,dependencies=('missing',))
  with self.assertRaises(ServiceConfigurationError):r.build()
  self.assertEqual(called,[])
 def test_cycle_fails_before_factories(self):
  called=[];r=ServiceRegistry();r.register('a',lambda d:called.append(1),dependencies=('b',));r.register('b',lambda d:0,dependencies=('a',))
  with self.assertRaises(ServiceConfigurationError):r.build()
  self.assertEqual(called,[])
 def test_dependency_view_is_read_only(self):
  r=ServiceRegistry();r.register('x',lambda d:1)
  def invalid(d):d['x']=2
  r.register('y',invalid,dependencies=('x',))
  with self.assertRaises(TypeError):r.build()
 def test_adapter_matches_existing_cli(self):
  root=Path(__file__).resolve().parents[1]
  direct=json.loads(subprocess.run([sys.executable,str(root/'run_simulation.py'),'--seed','5','--rounds','2'],capture_output=True,text=True,check=True).stdout)
  self.assertEqual(run(seed=5,rounds=2),direct)
 def test_legacy_adapter_runs_both_decks(self):
  for deck in ('premium','budget'):
   result=run(deck,seed=4,rounds=1);self.assertEqual(result['deck'],deck);self.assertIsNone(result['safety_stop'])
 def test_deck_file_matches_preset(self):
  root=Path(__file__).resolve().parents[1]
  for deck in ('premium','budget'):
   path=root/'decklists'/('magnus_thousand_sons_v1_14_premium.txt' if deck=='premium' else 'magnus_thousand_sons_v1_13_budget.txt')
   result=json.loads(subprocess.run([sys.executable,str(root/'run_simulation.py'),'--deck-file',str(path),'--seed','4','--rounds','2'],capture_output=True,text=True,check=True).stdout)
   expected=run(deck,seed=4,rounds=2);result['deck']=deck
   self.assertEqual(result,expected)
 def test_deck_file_fails_closed(self):
  root=Path(__file__).resolve().parents[1]
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'deck.txt';path.write_text('Commander\n1 Magnus the Red\nLibrary\n99 Imaginary Card\n')
   result=subprocess.run([sys.executable,str(root/'run_simulation.py'),'--deck-file',str(path)],capture_output=True,text=True)
  self.assertNotEqual(result.returncode,0);self.assertIn('Unverified card identity',result.stderr)
if __name__=='__main__':unittest.main()
