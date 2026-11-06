"""Diagnostic-only overlay for pinned Gorge activated-ability target aborts.

Adds stderr observations at offer/announcement mismatch without altering
target legality, engine events, choices, or replay state. Refuses unknown source.
"""
from pathlib import Path
import argparse

def replace_once(source, old, new):
    if source.count(old) != 1 or new in source:
        raise ValueError("Pinned Gorge target code drifted; refuse diagnostic patch")
    return source.replace(old, new, 1)

def patch(root: Path):
    path = root / "engine/rules/cast_targets.go"
    src = path.read_text()
    src = replace_once(src, 'import (\n\t"strconv"', 'import (\n\t"fmt"\n\t"os"\n\t"strconv"')
    src = replace_once(src,
        '\tcandidates := e.castTargetCandidates(pc, excludeSelf, sa)\n',
        '\tcandidates := e.castTargetCandidates(pc, excludeSelf, sa)\n'
        '\tpreFilterTargets := len(candidates) // diagnostics only\n')
    old = '''\tif min > 0 && !e.targetChoiceFeasible(sa, candidates, min) {
\t\t// CR 601.2c: a proposal with fewer legal targets than its mandatory'''
    new = '''\tif min > 0 && !e.targetChoiceFeasible(sa, candidates, min) {
\t\tif pc.isAbility() {
\t\t\tfmt.Fprintf(os.Stderr, "GORGE_TARGET_ABORT_DIAG source=%d ability=%d x=%d min=%d max=%d pre_filter=%d post_filter=%d tap_parts=%v cost=%+v stack_obj=%d\\n",
\t\t\t\tpc.card, pc.ability, pc.x, min, max, preFilterTargets, len(candidates), pc.cost.TapPermanent, pc.cost, pc.stackObj)
\t\t}
\t\t// CR 601.2c: a proposal with fewer legal targets than its mandatory'''
    src = replace_once(src, old, new)
    path.write_text(src)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gorge", type=Path, required=True)
    patch(ap.parse_args().gorge)
