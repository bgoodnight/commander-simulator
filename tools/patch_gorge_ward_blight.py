"""Pinned Gorge overlay: do not ask for an impossible ward-Blight payment.

Scope: Gorge b78e4c8b16078f6decbc48875bba953ce5535b85,
engine/rules/ward.go; we never silently retarget or invent creatures.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

TARGET = '''\t\tcase beginWardPaymentBlight:
\t\t\t// Blight's cost is "a creature you control gets -N/-N"; unlike
\t\t\t// Waterbend and a tap cost it does not require that creature to be
\t\t\t// untapped (Auntie Ool, Cursewretch).
\t\t\treturn e.askWardObjects(rp, ctx, payer, "ward_blight", "Choose a creature to blight", 1, 1,
\t\t\t\te.wardPermanents(payer, ctx.Source, "Creature", false))'''

REPLACEMENT = '''\t\tcase beginWardPaymentBlight:
\t\t\t// Ward Blight requires an eligible creature controlled by the payer.
\t\t\t// If none remains after the player elects Pay, payment fails and
\t\t\t// ward counters the triggering spell/ability as for an unpaid cost.
\t\t\t// Never generate a mandatory Choose(1..1) with zero options.
\t\t\tids := e.wardPermanents(payer, ctx.Source, "Creature", false)
\t\t\tif len(ids) == 0 {
\t\t\t\treturn false, false
\t\t\t}
\t\t\treturn e.askWardObjects(rp, ctx, payer, "ward_blight", "Choose a creature to blight", 1, 1, ids)'''


def patched(source: str) -> str:
    if source.count(TARGET) != 1 or REPLACEMENT in source:
        raise ValueError("Pinned Gorge ward-Blight source changed; manual review required")
    return source.replace(TARGET, REPLACEMENT, 1)


def apply(path: Path) -> str:
    original = path.read_text(encoding="utf-8")
    revised = patched(original)
    path.write_text(revised, encoding="utf-8")
    return hashlib.sha256(revised.encode("utf-8")).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--gorge", type=Path, required=True)
    args = p.parse_args()
    target = args.gorge / "engine/rules/ward.go"
    print("GORGE_RULES_PATCH_SHA256=" + apply(target))


if __name__ == "__main__":
    main()
