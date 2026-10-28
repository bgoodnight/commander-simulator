"""Conservative implementation audit of the actual Magnus v1.6 inventory.

This audits code paths and declared limits, not independently verified complete
Oracle text. 'supported subset' never means a card works in every Magic context.
"""
import json
from collections import Counter
from pathlib import Path
from expanded import CombatTable
import integrated as v6

ROOT = Path(__file__).resolve().parent
PARTIAL = {
    'Magnus the Red': 'Flying, token discount and combat-hit token trigger live; commander damage and full Commander rules remain absent.',
    'Harmonic Prodigy': 'Wizard/Shaman trigger doubling live; prowess is absent.',
    'Storm-Kiln Artist': 'Cast/copy trigger descriptor creates Treasure; artifact-count power bonus and live spell-copy production absent.',
    'Baral, Chief of Compliance': 'Generic discount live; counter-triggered loot absent.',
    'Stormsplitter': 'Cast-trigger token copies use a declared subset; expiry is cleanup rather than a delayed end-step trigger.',
    'Arcane Adaptation': 'Additive Wizard types live in declared zones; unrestricted creature-type choice/layers absent.',
    'Brainstorm': 'Selection adapter; exact draw/put-back ordering and choices absent.',
    'Ponder': 'Selection adapter; exact look/reorder/shuffle choices absent.',
    'Preordain': 'Selection adapter; full scry choices absent.',
    'Telling Time': 'Selection adapter; exact hand/top/bottom choice sequence absent.',
    'Impulse': 'Selection adapter; exact look/choose/bottom choices absent.',
    'Arcane Denial': 'Counter live; printed delayed draw timing/choices incomplete.',
    'Flusterstorm': 'Counter subset; storm copies and pay-one choice absent.',
    'Fiery Islet': 'U/R mana and life cost live; sacrifice-to-draw activation absent.',
    'Otawara, Soaring City': 'Land mana live; channel absent.',
    'Sokenzan, Crucible of Defiance': 'Land mana live; channel absent.',
    'Riptide Laboratory': 'Land mana live; Wizard-bounce activation absent.',
    'Mystic Sanctuary': 'Mana/ETB adapter; complete Island-subtype condition and graveyard-to-top choice absent.',
    'Fabled Passage': 'Prior fetch/ETB adapter; not a priority-aware printed activated ability.',
    'Steam Vents': 'Mana/ETB adapter; printed land subtypes and full entry choice not audited.',
    'Training Center': 'Mana/ETB adapter; opponent-count entry condition not fully modeled.',
    'Stormcarved Coast': 'Mana/ETB adapter; printed land-count entry condition not fully modeled.',
    'Sulfur Falls': 'Mana/ETB adapter; Island/Mountain subtype entry condition not fully modeled.',
    'Spirebluff Canal': 'Mana/ETB adapter; printed land-count entry condition not fully modeled.',
    'Riverglide Pathway': 'Chosen U/R mana face adapter; full modal double-faced characteristics absent.',
}
SUPPORTED = {
    'Young Pyromancer': 'Body and instant/sorcery cast token trigger.',
    'Third Path Iconoclast': 'Body and noncreature cast artifact-Soldier trigger.',
    'Archmage Emeritus': 'Body and magecraft trigger descriptors; live casts tested, spell copies not yet produced.',
    'Goblin Electromancer': 'Body and generic instant/sorcery discount with colored-cost floor.',
    'Frantic Search': 'Atomic draw two/discard two/untap up to three lands; discard uses deterministic pilot selection.',
    'Abrade': 'Announced modes, three creature damage or artifact destruction; target recheck.',
    'Capsize': 'Permanent bounce, optional buyback three, additional-cost reduction, counter/fizzle destinations.',
    "An Offer You Can't Refuse": 'Noncreature spell counter and two actual source-ID Treasure tokens for its controller.',
    'Counterspell': 'Target spell frame and counter destination.',
    'Swan Song': 'Restricted spell target and flying Bird compensation.',
    'Pongify': 'Creature destruction, indestructible handling and Ape compensation.',
    'Mind Stone': 'Colorless source plus paid tap/sacrifice draw activation with source reservation.',
}
PRIORITIES = [
    ('P1', 'Exact selection and land rules', 'Selection spells and utility lands are already used; correct existing approximations before comparing decks.'),
    ('P1', 'Engine omissions and delayed triggers', 'Harmonic prowess, Storm-Kiln power, Baral loot and Stormsplitter expiry affect live board states.'),
    ('P2', 'Spell copying', 'Shared prerequisite for Twincast/Reiterate/Dualcaster/Sigil Tracer and magecraft/copy interactions.'),
    ('P2', 'Creature activations and tutoring', 'Patron Wizard/Voidmage, Spellseeker, Mystical Tutor and transmute need explicit legal choices and costs.'),
    ('P3', 'Graveyard casting, replacement/layer breadth and combos', 'Breach, alternate costs, type engines and candidate loops need reusable prerequisites and interruption tests.'),
]


def build():
    t = CombatTable(seed=12)
    quantities = {v6.DECK['commander']: 1, **v6.DECK['cards']}
    rows = []
    for name, quantity in quantities.items():
        spec = t.zones.specs['named:'+name]
        if spec.effect == 'unsupported':
            status = 'unsupported'; detail = 'No live registered printed effect; drawn/reported but excluded from legal casts.'
        elif name in PARTIAL:
            status = 'partial'; detail = PARTIAL[name]
        else:
            status = 'supported subset'
            detail = SUPPORTED.get(name, 'Declared U/R/colorless mana ability; source-ID payment, tap and applicable costs.'
                                   if name in v6.ROCKS else 'Declared land mana source; ordinary land-play timing.')
        rows.append(dict(name=name, quantity=quantity, status=status, effect=spec.effect, detail=detail,
                         catalog_type=v6.CAT[name]['type']))
    counts = Counter(r['status'] for r in rows)
    physical = Counter()
    for r in rows: physical[r['status']] += r['quantity']
    return dict(deck=v6.DECK['name'], milestone='v12', total_cards=sum(quantities.values()),
                unique_names=len(rows), unique_counts=dict(counts), physical_counts=dict(physical),
                meaning='Implementation audit, not full Oracle certification; includes commander and repeated basics.',
                priorities=[dict(priority=p, area=a, reason=r) for p,a,r in PRIORITIES], cards=rows)


def write():
    data = build(); (ROOT/'CARD_COVERAGE.json').write_text(json.dumps(data, indent=2)+'\n')
    lines = ['# Magnus v1.6 implementation coverage — v12', '',
             'Code-path audit of the actual 99 plus commander. Supported subset means the listed behavior is live; it is not full Oracle certification. Partial means a usable effect has known omissions. Unsupported cards are excluded from legal casts, not replaced by invented generic effects.', '',
             f"Inventory: {data['total_cards']} physical cards; {data['unique_names']} distinct names. Statuses include commander and repeated basics.", '',
             '| Status | Distinct names | Physical cards |', '|---|---:|---:|']
    for status in ('supported subset', 'partial', 'unsupported'):
        lines.append(f"| {status} | {data['unique_counts'].get(status,0)} | {data['physical_counts'].get(status,0)} |")
    lines += ['', '## Triage', '', '| Priority | Area | Reason |', '|---|---|---|']
    lines += [f'| {p} | {a} | {r} |' for p,a,r in PRIORITIES]
    lines += ['', 'The combat expansion does not add named cards to the deck. First/double strike and trample are validated with explicitly synthetic combat fixtures; those results must not be interpreted as newly complete deck-card implementations.', '',
              '## Per-card evidence and limits', '', '| Card | Qty | Status | Live behavior / gap |', '|---|---:|---|---|']
    lines += [f"| {r['name']} | {r['quantity']} | {r['status']} | {r['detail']} |" for r in data['cards']]
    lines += ['', 'Evidence: v6 named-spec adapter, v7 descriptors, v9b live registration, v9c mana provider, v10 response/activation providers, v11 card expansion and v12 combat. Historical supported/approx counters measure chosen effects and should not be treated as whole-card completion percentages.', '']
    (ROOT/'CARD_COVERAGE.md').write_text('\n'.join(lines))
    return data


if __name__ == '__main__':
    data = write(); print(json.dumps({k:data[k] for k in ('total_cards','unique_names','unique_counts','physical_counts')}, indent=2))
