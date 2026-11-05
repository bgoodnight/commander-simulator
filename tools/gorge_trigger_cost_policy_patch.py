"""Patch the exact pinned Gorge botpolicy for an isolated trigger-cost pilot A/B.

Do not edit the upstream repository or baseline pilot results. Refuse to patch
if the expected source anchor has changed.
"""
from pathlib import Path
import argparse

ANCHOR = '''\t\tcase "x":
\t\t\tin.Choices = []int{d.Options[len(d.Options)-1].Index} // the most it can pay for
'''
INSERT = '''\t\tcase "trigger_cost_x":
\t\t\t// Announced trigger-body X (CR 603.12): choose the highest
\t\t\t// engine-offered payable amount, rather than the default option
\t\t\t// X=0. This is the same generic policy as ordinary cast X.
\t\t\tbest := d.Options[0]
\t\t\tfor _, o := range d.Options {
\t\t\t\tif o.Kind == "trigger_cost_x" && o.Amount > best.Amount {
\t\t\t\t\tbest = o
\t\t\t\t}
\t\t\t}
\t\t\tin.Choices = []int{best.Index}
\t\tcase "trigger_cost_pay", "trigger_cost_decline":
\t\t\t// Pay an already-announced trigger cost when a legal pay choice
\t\t\t// is offered. If no pay choice is offered, decline.
\t\t\tin.Choices = []int{d.Options[0].Index}
\t\t\tfor _, o := range d.Options {
\t\t\t\tif o.Kind == "trigger_cost_pay" {
\t\t\t\t\tin.Choices = []int{o.Index}
\t\t\t\t\tbreak
\t\t\t\t}
\t\t\t}
'''

def patch(path:Path):
    source=path.read_text()
    if source.count(ANCHOR)!=1:
        raise ValueError("Pinned Gorge source changed; trigger-cost patch refused")
    path.write_text(source.replace(ANCHOR,INSERT+ANCHOR))
    print("Applied isolated generic trigger-cost choice patch to pinned Gorge botpolicy")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("path",type=Path)
    patch(p.parse_args().path)
