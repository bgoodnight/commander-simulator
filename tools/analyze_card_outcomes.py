"""Explore modeled win-by-horizon associations with kept opening-hand card flags.

Standard-library-only: bootstrap shallow trees for *screening*, followed by
ridge logistic regression and held-out validation by entire simulation seed.
No post-selection p-values, causal claims or real Commander win-rate claims.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
from random import Random

FORMAT = "commander-opening-hand-discovery-v1"
SOURCE_FORMAT = "commander-modeled-outcomes-v1"
OUTCOMES = frozenset({"win", "loss", "draw", "unresolved"})


def _records(batches):
    if not batches:
        raise ValueError("Expected nonempty authentic outcome batches")
    identity, rows, used = None, [], set()
    for batch in batches:
        if (batch.get("format") != SOURCE_FORMAT
                or batch.get("schema_version") != 1
                or batch.get("opponent_fidelity") !=
                   "abstract_opponent_pressure_not_card_exact"
                or batch.get("outcomes_are_competitive_win_rates") is not False):
            raise ValueError("Not an authentic modeled outcome batch")
        key = (batch["deck_key"], batch["deck_sha256"],
               batch["requested_rounds"], batch.get("pilot_style"),
               batch.get("provisional_mode"),
               json.dumps(batch.get("pilot_archetype"), sort_keys=True))
        if identity is None:
            identity = key
        elif identity != key:
            raise ValueError("Mixed deck revisions, horizons, or pilot settings")
        scenario = batch.get("scenario")
        if not isinstance(scenario, str) or not scenario:
            raise ValueError("Missing recorded scenario")
        for run in batch.get("runs", []):
            seed = run.get("seed")
            outcome = run.get("outcome", {}).get("status")
            hand = run.get("opening_hand")
            if not isinstance(seed, int) or seed < 0 or (scenario, seed) in used:
                raise ValueError("Invalid or duplicate simulation seed")
            used.add((scenario, seed))
            if outcome not in OUTCOMES:
                raise ValueError("Missing or unevaluated modeled outcome")
            if (not isinstance(hand, list) or len(hand) != 7
                    or any(not isinstance(c, str) or not c.strip() for c in hand)):
                raise ValueError("Opening-hand evidence missing: rerun with new exporter")
            opponent_roles = run.get("opponent_roles")
            if not isinstance(opponent_roles, dict):
                raise ValueError("Missing opponent seat provenance")
            roles = [opponent_roles.get(str(i), opponent_roles.get(i))
                     for i in (1, 2, 3)]
            if any(not isinstance(x, str) or not x for x in roles):
                raise ValueError("Missing three opponent types")
            rows.append({"seed": seed, "scenario": scenario,
                         "hand": frozenset(hand), "roles": Counter(roles),
                         "win": int(outcome == "win")})
    return rows, identity


def _split(rows, seed=2026, fraction=0.25):
    seeds = sorted({row["seed"] for row in rows})
    if len(seeds) < 20:
        raise ValueError("Need at least 20 distinct simulation seeds")
    Random(seed).shuffle(seeds)
    holdout = set(seeds[:max(1, round(fraction*len(seeds)))])
    return ([r for r in rows if r["seed"] not in holdout],
            [r for r in rows if r["seed"] in holdout])


def _impurity(rows):
    if not rows:
        return 0.0
    p = sum(row["win"] for row in rows) / len(rows)
    return 2 * p * (1-p)


def _screen(train, candidates, *, seed=2026, trees=64, min_leaf=7):
    """Bagged depth-two CART. Bootstrap complete seed groups to avoid leakage."""
    rng = Random(seed)
    groups = defaultdict(list)
    for row in train:
        groups[row["seed"]].append(row)
    seeds = sorted(groups)
    gains = Counter()
    mtry = min(len(candidates), max(4, math.isqrt(len(candidates))))
    for _ in range(trees):
        sample = [row for __ in seeds for row in groups[rng.choice(seeds)]]
        def grow(node, depth):
            if depth >= 2 or len(node) < 2*min_leaf:
                return
            best = (0.0, None, None, None)
            for card in rng.sample(candidates, mtry):
                present = [r for r in node if card in r["hand"]]
                absent = [r for r in node if card not in r["hand"]]
                if min(len(present), len(absent)) < min_leaf:
                    continue
                gain = (_impurity(node) -
                        (len(present)*_impurity(present) +
                         len(absent)*_impurity(absent))/len(node))
                if gain > best[0]:
                    best = (gain, card, present, absent)
            gain, card, yes, no = best
            if card is None:
                return
            gains[card] += gain*len(node)/len(sample)/trees
            grow(yes, depth+1)
            grow(no, depth+1)
        grow(sample, 0)
    return gains


def _solve(matrix, vector):
    """Pivoted Gaussian elimination for small ridge-regularized systems."""
    n = len(vector)
    a = [list(row)+[vector[i]] for i, row in enumerate(matrix)]
    for j in range(n):
        best = max(range(j, n), key=lambda k: abs(a[k][j]))
        if abs(a[best][j]) < 1e-10:
            raise ValueError("Singular regression design")
        a[j], a[best] = a[best], a[j]
        pivot = a[j][j]
        a[j] = [x/pivot for x in a[j]]
        for i in range(n):
            if i == j:
                continue
            mul = a[i][j]
            for k in range(j, n+1):
                a[i][k] -= mul*a[j][k]
    return [row[-1] for row in a]


def _prob(eta):
    if eta >= 0:
        return 1/(1+math.exp(-min(eta, 35)))
    e = math.exp(max(-35, eta))
    return e/(1+e)


def _design(rows, cards, scenarios, roles):
    return [[1.0] +
            [float(r["scenario"] == s) for s in scenarios[1:]] +
            [float(r["roles"][role]) for role in roles[:-1]] +
            [float(card in r["hand"]) for card in cards]
            for r in rows]


def _ridge_logistic(x, labels, penalty=3.0):
    d = len(x[0])
    beta = [0.0]*d
    for _ in range(40):
        grad = [0.0]*d
        hess = [[0.0]*d for _ in range(d)]
        for row, y in zip(x, labels):
            probability = _prob(sum(b*v for b, v in zip(beta, row)))
            weight = max(1e-8, probability*(1-probability))
            for j in range(d):
                grad[j] += row[j]*(y-probability)
                for k in range(j+1):
                    hess[j][k] += weight*row[j]*row[k]
        for j in range(d):
            if j:
                grad[j] -= penalty*beta[j]
                hess[j][j] += penalty
            else:
                hess[j][j] += 1e-8
            for k in range(j):
                hess[k][j] = hess[j][k]
        step = _solve(hess, grad)
        scale = max(1, max(abs(s) for s in step)/2)
        beta = [b+s/scale for b, s in zip(beta, step)]
        if max(abs(s)/scale for s in step) < 1e-7:
            break
    return beta


def _brier(coefficients, x, labels):
    return sum((_prob(sum(b*v for b, v in zip(coefficients, row)))-y)**2
               for row, y in zip(x, labels))/len(labels)


def analyze(batches, *, min_presence=8, top_k=8, trees=64, seed=2026):
    if not 2 <= min_presence or not 1 <= top_k <= 20 or trees < 1:
        raise ValueError("Invalid screening settings")
    rows, identity = _records(batches)
    train, test = _split(rows, seed=seed)
    wins = sum(row["win"] for row in train)
    if min(wins, len(train)-wins) < 5:
        raise ValueError("Too few modeled wins or nonwins to fit")
    scenarios = sorted({r["scenario"] for r in rows})
    role_names = sorted({role for r in rows for role in r["roles"]})
    counts = Counter(card for r in train for card in r["hand"])
    eligible = sorted(card for card, n in counts.items()
                      if min_presence <= n <= len(train)-min_presence)
    if not eligible:
        raise ValueError("No opening-hand cards pass minimum support")
    importance = _screen(train, eligible, seed=seed, trees=trees)
    selected = sorted((c for c in eligible if importance[c] > 0),
                      key=lambda c: (-importance[c], c))[:top_k]
    if not selected:
        raise ValueError("No informative card splits in training data")
    y_train = [r["win"] for r in train]
    y_test = [r["win"] for r in test]
    xb = _design(train, [], scenarios, role_names)
    xb_test = _design(test, [], scenarios, role_names)
    xf = _design(train, selected, scenarios, role_names)
    xf_test = _design(test, selected, scenarios, role_names)
    baseline = _ridge_logistic(xb, y_train)
    full = _ridge_logistic(xf, y_train)
    card_offset = len(xf[0])-len(selected)
    effects = []
    for i, card in enumerate(selected):
        exposed = [r for r in train if card in r["hand"]]
        effects.append({
            "card": card, "train_present": len(exposed),
            "train_wins_when_present": sum(r["win"] for r in exposed),
            "tree_gain": round(importance[card], 6),
            "ridge_odds_ratio": round(math.exp(full[card_offset+i]), 3)})
    brier_base = _brier(baseline, xb_test, y_test)
    brier_full = _brier(full, xf_test, y_test)
    return {
        "format": FORMAT, "schema_version": 1, "exploratory": True,
        "deck_key": identity[0], "deck_sha256": identity[1],
        "requested_rounds": identity[2],
        "pilot_style": identity[3], "provisional_mode": identity[4],
        "scenarios": scenarios, "opponent_types": role_names,
        "outcome": "modeled_win_by_fixed_horizon",
        "features": "kept_opening_hand_binary",
        "sample": {"games": len(rows),
                   "distinct_seeds": len({r["seed"] for r in rows}),
                   "wins": sum(r["win"] for r in rows),
                   "train_games": len(train), "test_games": len(test),
                   "train_wins": wins, "test_wins": sum(y_test),
                   "eligible_cards": len(eligible)},
        "screen": {"method": "seed_bootstrapped_depth_two_trees",
                   "trees": trees, "top_k": top_k,
                   "selected_in_training_only": True},
        "logistic": {"method": "ridge_logistic", "penalty": 3.0,
                     "fixed_controls": ["scenario", "opponent_type_counts"],
                     "card_effects": effects},
        "validation": {
            "split": "heldout_seed_groups",
            "control_only_brier": round(brier_base, 5),
            "with_cards_brier": round(brier_full, 5),
            "cards_improve_heldout_brier": brier_full < brier_base},
        "limitations": [
            "Exploratory associations, not card effects or real Commander win rates.",
            "No post-selection p-values or naive confidence intervals.",
            "Unresolved means no modeled win by horizon, not a loss.",
            "A card in hand need not be played; later-drawn cards are not modeled.",
            "Same-seed scenarios are clustered for holdout, not independent draws.",
            "Interpret selected odds ratios with shrinkage and selection bias."
        ]}
    

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--min-presence", type=int, default=8)
    p.add_argument("--top-k", type=int, default=8)
    p.add_argument("--trees", type=int, default=64)
    args = p.parse_args(argv)
    batches = [json.loads(path.read_text(encoding="utf-8"))
               for path in sorted(args.source.glob("*.json"))]
    result = analyze(batches, min_presence=args.min_presence,
                     top_k=args.top_k, trees=args.trees)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n",
                           encoding="utf-8")
    print(json.dumps({"output": str(args.output),
                      "selected_cards": len(result["logistic"]["card_effects"]),
                      "validation": result["validation"]}, indent=2))


if __name__ == "__main__":
    main()
