"""Canonical v1.13 deck adapter; unknown card metadata fails closed."""
from pathlib import Path
from collections import Counter
import random, re, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v17_tutor'))
from tutor_table import TutorTable
from state import ZoneDetailedPlayer
import integrated as v6
import simulation as base

DECK_PATH=Path(__file__).resolve().parents[2]/'decklists'/'magnus_thousand_sons_v1_13_budget.txt'

def load_deck():
    section=None; cards=Counter()
    for raw in DECK_PATH.read_text().splitlines():
        line=raw.strip()
        if not line: continue
        if line in ('Commander','Library'):section=line;continue
        match=re.fullmatch(r'(\d+) (.+)',line)
        if not match or section is None:raise ValueError('Invalid decklist line: '+line)
        qty=int(match.group(1));name=match.group(2)
        if qty<1:raise ValueError('Invalid quantity')
        cards[(section,name)]+=qty
    if cards.get(('Commander','Magnus the Red'))!=1 or sum(v for (s,_),v in cards.items() if s=='Commander')!=1:
        raise ValueError('Expected exactly Magnus as commander')
    if sum(cards.values())!=100:raise ValueError('Expected 100 physical cards')
    for (section,name),qty in cards.items():
        if qty>1 and name not in {'Island','Mountain'}:raise ValueError('Duplicate nonbasic card '+name)
    return cards

def card_spec(name):
    if name in v6.CAT:return v6.named_spec(name)
    return base.CardSpec(name,name,0,'unknown','unsupported',{'coverage':'unverified'}, {})

class BudgetPlayer(ZoneDetailedPlayer):
    def __init__(self,seat,seed,zones):
        base.Player.__init__(self,seat,'magnus',seed,[],v6.MagnusPilot())
        self.zones=zones;self.payment_policy=v6.ColoredPayment()
        self.ready_sources=[];self.floating=(0,0,0);self.commander_casts=0
        self.payments=[];self.treasures=0;self.coverage=Counter();self.unsupported_seen=Counter()
        self.block_policy='never'
        cards=load_deck();library=[]
        for (section,name),qty in cards.items():
            if section=='Library':library.extend([card_spec(name)]*qty)
        random.Random(seed+601).shuffle(library)
        for card in library:zones.add_spec(card,seat,detailed=True)
        zones.add_spec(v6.named_spec('Magnus the Red'),seat,'command',detailed=True)
        # Older provider installers expect these definitions even when absent.
        for name in ('Abrade','Arcane Adaptation'):
            if 'named:'+name not in zones.specs:zones.register(v6.named_spec(name),detailed=True)
        self.draw(7)
        if not 2 <= sum(c.kind=='land' for c in self.hand) <= 5:self.mulligan()

class BudgetTable(TutorTable):
    detailed_player_class=BudgetPlayer

    def tutor_library_known(self, seat):
        return all('unknown' not in self.rules.get(oid).types for oid in self.zones.ids(seat, 'library'))

    def priority_choices(self, seat):
        choices=super().priority_choices(seat)
        return tuple(c for c in choices if not (c.kind == 'spell' and c.action.source == 'Mystical Tutor'
                                                and not self.tutor_library_known(seat)))

    def cast(self, action):
        if action.source == 'Mystical Tutor' and not self.tutor_library_known(action.actor):
            raise NotImplementedError('Mystical Tutor requires verified library card types')
        return super().cast(action)
