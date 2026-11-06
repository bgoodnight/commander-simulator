"""Strict experimental Gorge overlay: honor ChangeZone AnyNumber$ True.

The pinned Gorge hidden public-origin picker already supports an arbitrary
number of cards under a WithTotalCMC budget for ChooseFromDefined. This overlay
extends that same mechanism to an explicitly scripted AnyNumber$ True
(Technomancer), without inventing a one-card cap. Only the pinned source
anchors are accepted; no upstream checkout is modified.
"""
from __future__ import annotations
import argparse
from pathlib import Path

FIELDS='\tChangeNum          ParamText\n'
FIELDS_NEW='\tAnyNumber          bool // explicit AnyNumber$ True (Technomancer)\n'+FIELDS
KNOWN='\t"AlreadyRevealed", "AlternateCost",\n'
KNOWN_NEW='\t"AlreadyRevealed", "AlternateCost", "AnyNumber",\n'
READ='\tcn, cnOK := sa.Param(cards.PKChangeNum)\n'
READ_NEW='\tp.AnyNumber = isTrue(sa.ParamStr("AnyNumber"))\n'+READ
CHOOSER='\tchooseFromAll := hasChooseFromDefined && cz.ChangeNum.Text == ""'
CHOOSER_NEW='\tchooseFromAll := (hasChooseFromDefined || cz.AnyNumber) && cz.ChangeNum.Text == ""'

def replace_once(text:str,needle:str,replacement:str)->str:
    if text.count(needle)!=1 or replacement in text:
        raise ValueError("Expected pinned Gorge source anchor not found exactly once")
    return text.replace(needle,replacement,1)

def patch(root:Path)->None:
    compiler=root/"engine/effects/changezone_params.go"
    chooser=root/"engine/effects/zone_hidden.go"
    a=compiler.read_text()
    a=replace_once(a,FIELDS,FIELDS_NEW)
    a=replace_once(a,KNOWN,KNOWN_NEW)
    a=replace_once(a,READ,READ_NEW)
    b=replace_once(chooser.read_text(),CHOOSER,CHOOSER_NEW)
    # Both changes are validated before either is written.
    compiler.write_text(a)
    chooser.write_text(b)
    print("Applied strict AnyNumber true support to Gorge public-origin ChangeZone picker")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--gorge",required=True,type=Path)
    patch(p.parse_args().gorge)
