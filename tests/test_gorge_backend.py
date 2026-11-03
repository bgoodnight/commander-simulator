"""Guard the optional gorge Python facade without needing Go in unit tests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from commander_sim.gorge_backend import run_gorge_batch,GorgeBackendError


class GorgeBackendTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        (self.root/"probe").write_text("")
        (self.root/"corpus").mkdir()
        (self.root/"decks").mkdir()
        self.names=["mortarion_current","magnus_premium","necron_dynasties",
                    "wretched_ranks"]
        for name in self.names:
            (self.root/"decks"/(name+".json")).write_text("{}")
        self.kw={"binary":self.root/"probe","corpus":self.root/"corpus",
                 "deck_dir":self.root/"decks","decks":self.names,
                 "games":2,"seed":50}

    def tearDown(self):
        self.tmp.cleanup()

    def fake_result(self):
        return "\n".join(json.dumps({
            "seed":50+i,"decks":self.names,"policies":["bot"]*4,
            "finished":True,"replay_verified":True,"events":2000,
            "turns":23,"elapsed_seconds":0.03}) for i in range(2))

    def test_python_backend_runs_without_copied_rules(self):
        with patch("commander_sim.gorge_backend.subprocess.run",
                   return_value=SimpleNamespace(returncode=0,
                       stdout=self.fake_result(),stderr="")) as call:
            result=run_gorge_batch(**self.kw,
                 pilot="forge-heuristic",hero_pilot="lethal-pressure")
        self.assertEqual(result["schema"],"gorge-backend-batch-v1")
        self.assertEqual(len(result["games"]),2)
        argv=call.call_args.args[0]
        self.assertEqual(argv[argv.index("-pilot")+1],"forge-heuristic")
        self.assertEqual(argv[argv.index("-hero-pilot")+1],"lethal-pressure")
        self.assertEqual(argv[argv.index("-verify=true")],"-verify=true")

    def test_fails_closed_for_unknown_bot_and_unavailable_deck(self):
        with self.assertRaises(ValueError):
            run_gorge_batch(**self.kw,pilot="unsupported-ai")
        with self.assertRaises(FileNotFoundError):
            run_gorge_batch(**{**self.kw,"decks":self.names[:-1]+["absent"]})

    def test_fails_closed_on_missing_or_unverified_games(self):
        with patch("commander_sim.gorge_backend.subprocess.run",
                   return_value=SimpleNamespace(returncode=2,
                       stdout=self.fake_result(),stderr="failed")):
            with self.assertRaisesRegex(GorgeBackendError,"code 2"):
                run_gorge_batch(**self.kw)
        bad=json.loads(self.fake_result().splitlines()[0])
        bad["replay_verified"]=False
        with patch("commander_sim.gorge_backend.subprocess.run",
                   return_value=SimpleNamespace(returncode=0,
                       stdout="\n".join([json.dumps(bad),
                              self.fake_result().splitlines()[1]]),
                       stderr="")):
            with self.assertRaisesRegex(GorgeBackendError,"replay"):
                run_gorge_batch(**self.kw)

    def test_timeout_is_failure_not_hypothetical_result(self):
        import subprocess
        with patch("commander_sim.gorge_backend.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd=["probe"],timeout=1)):
            with self.assertRaisesRegex(GorgeBackendError,"timed out"):
                run_gorge_batch(**self.kw)


if __name__=="__main__":
    unittest.main()
