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
    # Diagnostic checkpoints do not affect candidate selection or game state.
    checkpoints = [
        ('\tcandidates = e.affordableTargetCandidates(pc, candidates)\n', 'affordable'),
        ('\tcandidates = e.targetBoundCandidates(pc.player, pc.card, &pc.cost, pc.isAbility(), candidates)\n', 'bound_cost'),
        ('\tcandidates, powerCap, powerCapped := e.totalPowerCappedCandidates(candidates, pc.player, pc.card, sa, pc.x)\n', 'power_cap'),
        ('\tcandidates, cmcCap, cmcCapped := e.totalCMCCappedCandidates(candidates, pc.player, pc.card, sa, pc.x)\n', 'cmc_cap'),
    ]
    for old, stage in checkpoints:
        if src.count(old) != 1:
            raise ValueError("Pinned target filter anchor changed: " + stage)
        new = old + (
            '\tif pc.isAbility() && min > 0 {\n'
            '\t\tfmt.Fprintf(os.Stderr, "GORGE_TARGET_STAGE source=%d ability=%d x=%d stage=' + stage +
            ' candidates=%d\\n", pc.card, pc.ability, pc.x, len(candidates))\n'
            '\t}\n'
        )
        src = replace_once(src, old, new)
    # Pinpoint why an ability target was dropped by the 601.2c affordability
    # check; no payment, candidate selection, or engine state is modified.
    pricing = root / "engine/rules/cast_pricing.go"
    full = pricing.read_text()
    start = full.index("func (e *Engine) affordableTargetCandidates(")
    end = full.index("\n// manaToPay", start)
    body = full[start:end]
    before = body
    checks = [
        ('if !pay.NonManaCastable(asPayer(e), pc.player, pc.card, cost, pc.isAbility(), tapCostSAKind(e.pcAbility(pc))) {\n\t\t\tcontinue',
         'nonmana'),
        ('if cost.Life > 0 && cost.Life > pl.Life {\n\t\t\tcontinue',
         'life'),
        ('if !cost.HasManaPayment() {\n\t\t\tcontinue',
         'no_mana_payment'),
        ('if !targetDiscount && !e.hasUntappedManaSource(pc.player) {\n\t\t\tcontinue',
         'no_mana_source'),
    ]
    for old, reason in checks:
        new = old.replace('\n\t\t\tcontinue',
            '\n\t\t\tif pc.isAbility() { fmt.Fprintf(os.Stderr, "GORGE_AFFORD_DROP source=%d x=%d target=%d reason=' +
            reason + ' generic=%d life=%d\\n", pc.card, pc.x, candidate.obj, cost.Generic, cost.Life) }\n\t\t\tcontinue')
        body = replace_once(body, old, new)
    anchor_reach = (
        'out = append(out, candidate)\n'
        '\t\t\t}\n'
        '\t\t} else {\n'
        '\t\t\tout = append(out, candidate)\n'
        '\t\t}\n'
    )
    if body.count(anchor_reach) != 1:
        raise ValueError("Pinned affordability window branch changed")
    newer_reach = (
        'out = append(out, candidate)\n'
        '\t\t\t} else if pc.isAbility() {\n'
        '\t\t\t\tfmt.Fprintf(os.Stderr, "GORGE_AFFORD_DROP source=%d x=%d target=%d reason=window_unreachable generic=%d life=%d census=%t discount=%t\\n", pc.card, pc.x, candidate.obj, cost.Generic, cost.Life, censusComplete, targetDiscount)\n'
        '\t\t\t}\n'
        '\t\t} else {\n'
        '\t\t\tout = append(out, candidate)\n'
        '\t\t}\n'
    )
    body = replace_once(body, anchor_reach, newer_reach)
    full = full[:start] + body + full[end:]
    full = replace_once(full, '\t"fmt"\n', '\t"fmt"\n\t"os"\n')
    pricing.write_text(full)
    path.write_text(src)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gorge", type=Path, required=True)
    patch(ap.parse_args().gorge)
