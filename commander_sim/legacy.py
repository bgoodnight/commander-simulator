"""Explicit isolation adapter while historical modules still share names."""
import json,subprocess,sys
from pathlib import Path

_ROOT=Path(__file__).resolve().parents[1]
def run(deck='premium',*,seed=0,rounds=8):
    if deck not in ('premium','budget'):raise ValueError('Unknown legacy deck')
    if not isinstance(seed,int) or not isinstance(rounds,int) or rounds<1:raise ValueError('Invalid seed or round limit')
    result=subprocess.run([sys.executable,str(_ROOT/'run_simulation.py'),'--deck',deck,'--seed',str(seed),'--rounds',str(rounds)],text=True,capture_output=True,check=True)
    return json.loads(result.stdout)
