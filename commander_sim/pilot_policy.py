"""Deterministic, deck-derived tactical preference over ALREADY LEGAL actions.

The physical kernel, reviewed card handlers and mana planner determine whether
an action exists and is payable. This module only orders supplied candidates.
No commander name, card-name whitelist, random tie-breaking or inferred Oracle
permission appears here. Generic strategy flags come from printed deck contents
and current physical board state, not from a hard-coded deck registry.

Personalities alter small, documented score offsets; they do not unlock effects.
"""
from dataclasses import dataclass
import re

STYLES = ("adaptive", "balanced", "engine", "tempo", "conservative")
_TRIGGERS = re.compile(
    r"whenever you (?:cast|copy) (?:an? |one or more )?(?:instant|sorcery)"
    r"|magecraft|whenever you cast an instant or sorcery", re.I)
_GRAVE = re.compile(
    r"\bgraveyard\b|\bmill (?:a |one |two |three |\d+)|\bunearth\b"
    r"|\bescape\b|\bflashback\b", re.I)
_SACRIFICE = re.compile(r"\bsacrifice\b|\bwhenever (?:a|another|one or more) "
                        r"[^\n]{0,85}\bdies\b", re.I)
_TOKEN = re.compile(r"\bcreate\b[^\n]{0,130}\btokens?\b|\bpopulate\b", re.I)
_ARTIFACT = re.compile(
    r"\bartifact(?:s)?\b|\baffinity for artifacts\b", re.I)
_AGGRESSION = re.compile(r"\bhaste\b|\bmenace\b|\bdouble strike\b|\btrample\b",re.I)

_FEATURE_RULES = {
    "spell_engine": _TRIGGERS,
    "graveyard": _GRAVE,
    "sacrifice": _SACRIFICE,
    "tokens": _TOKEN,
    "artifacts": _ARTIFACT,
    "combat": _AGGRESSION,
}
# Pure preferences in the *decision layer*. Smaller shifts than a missing
# printed effect can never be used to bypass source verification.
_PERSONALITY = {
    "balanced": {},
    "adaptive": {},   # Auto uses observed density of the actual deck.
    "engine": {"engine":8,"draw":4,"reanimate":4,"ramp":2,"combat":-4},
    "tempo": {"engine":-2,"draw":-3,"ramp":-2,"combat":8,"removal":5},
    "conservative": {"ramp":5,"draw":5,"removal":7,"combat":-5,"reanimate":-3},
}
_BASE = {
    "ramp":61,"engine":55,"creature":46,"commander":46,
    "artifact":44,"enchantment":43,"draw":40,"tutor":39,
    "reanimate":41,"removal":37,"combat":39,"token":40,
    "ritual":80,"other":34,
}


@dataclass(frozen=True)
class DeckSignals:
    nonland_cards: int
    counts: tuple[tuple[str,int],...]
    keywords: tuple[str,...]

    def __post_init__(self):
        if (type(self.nonland_cards) is not int or self.nonland_cards<0
                or not isinstance(self.counts,tuple)
                or any(type(k) is not str or type(v) is not int or v<0
                       for k,v in self.counts)
                or not isinstance(self.keywords,tuple)):
            raise ValueError("Invalid deck-derived signals")

    def count(self,category):
        return dict(self.counts).get(category,0)

    def dense(self,category):
        # At least four actual cards and at least ~one in fourteen nonlands.
        return (self.count(category)>=4
                and self.count(category)*14>=max(1,self.nonland_cards))

    def as_dict(self):
        return {"nonland_cards":self.nonland_cards,
                "counts":dict(self.counts),
                "dense_synergies":[k for k,_ in self.counts if self.dense(k)],
                "keywords":list(self.keywords)}


def infer_deck_signals(deck_cards,catalog):
    """Source-pinned printed traits; (section,name,quantity) deck entries.

    The discovery text only sets strategic weights; never card execution.
    Uses quantities for actual deck composition, not number of unique names.
    """
    if not isinstance(catalog,dict):
        raise TypeError("Deck catalog required")
    counts={k:0 for k in _FEATURE_RULES}
    keywords=set()
    nonlands=0
    for section,name,quantity in deck_cards:
        if type(quantity) is not int or quantity<1:
            raise ValueError("Invalid deck quantity")
        row=catalog.get(name)
        if (not isinstance(row,dict)
                or not isinstance(row.get("type_line"),str)
                or not isinstance(row.get("oracle_text"),str)
                or not row.get("oracle_id")):
            # Multi-faced or unverified definitions do not influence behavior.
            continue
        types=row["type_line"].split(" — ",1)[0].lower().split()
        if "land" in types:
            continue
        nonlands+=quantity
        text=row["oracle_text"]
        for category,pattern in _FEATURE_RULES.items():
            if pattern.search(text):
                counts[category]+=quantity
        for word in ("haste","flying","lifelink","menace","deathtouch",
                     "vigilance","trample"):
            if re.search(r"\b"+word+r"\b",text,re.I):
                keywords.add(word)
    return DeckSignals(nonlands,tuple(sorted(counts.items())),
                       tuple(sorted(keywords)))


@dataclass(frozen=True)
class PilotContext:
    round: int
    life: int
    hand_size: int
    lands: int
    mana_sources: int
    graveyard_creatures: int
    friendly_creatures: int
    opposing_creatures: int

    def __post_init__(self):
        if (any(type(v) is not int for v in self.__dict__.values())
                or self.round<1 or self.mana_sources<0 or self.lands<0
                or self.hand_size<0 or self.friendly_creatures<0
                or self.opposing_creatures<0):
            raise ValueError("Invalid physical pilot state")


@dataclass(frozen=True)
class RankedChoice:
    score: int
    category: str
    factors: tuple[str,...]

    def as_dict(self):
        return {"score":self.score,"category":self.category,
                "factors":list(self.factors)}


def _category(kind,raw):
    """Map legal driver action kind plus verified printed text to roles."""
    text=raw.get("oracle_text","") if isinstance(raw,dict) else ""
    if not isinstance(text,str):
        text=""
    if kind=="commander":
        return "commander"
    if kind=="ritual":
        return "ritual"
    if kind=="removal_spell":
        return "removal"
    if kind=="graveyard_spell":
        return "reanimate"
    if kind=="draw_spell" or "draw a card" in text and kind=="provisional_spell":
        return "draw"
    if kind=="tutor":
        return "tutor"
    if kind=="token_spell" or "create " in text and " token" in text and kind=="provisional_spell":
        return "token"
    if kind=="artifact":
        mana_text=bool(re.search(r"\{T\}: Add|\{T\}: Add",text,re.I))
        if mana_text or re.search(r"\badd \{[WUBRGC]\}",text,re.I):
            return "ramp"
        # Non-mana artifacts are still meaningful permanents, not "other".
        return "artifact"
    if kind in {"creature","enchantment"}:
        if _TRIGGERS.search(text) or re.search(
                r"whenever [^\n]{0,100}(?:dies|sacrifice)|"
                r"at the beginning of your (?:upkeep|end step)",text,re.I):
            return "engine"
        return "creature" if kind=="creature" else "enchantment"
    if kind=="common_spell":
        if "draw " in text.lower():
            return "draw"
        if _TOKEN.search(text):
            return "token"
    return "other"


def rank_legal_action(kind,raw,context,signals,*,style="adaptive"):
    """Return deterministic utility and explanations for a legal option.

    Affordability, targeting, summoning sickness and effect admission MUST
    already have been established by the source-paid runner.
    """
    if style not in STYLES:
        raise ValueError("Unknown pilot personality")
    if not isinstance(context,PilotContext) or not isinstance(signals,DeckSignals):
        raise TypeError("A complete physical context and deck signals are required")
    category=_category(kind,raw)
    score=_BASE[category]
    factors=[f"base:{category}"]
    if category=="ritual":
        # Runner only admits rituals after a legal spell-unlock preview.
        factors.append("reviewed_spell_unlock_only")
    # Constraints induced by *current state*, never a name lookup.
    if context.round<=5 and context.mana_sources<=4 and category=="ramp":
        score+=22
        factors.append("early_mana_development")
    if context.mana_sources>=9 and category=="ramp":
        score-=19
        factors.append("late_ramp_diminishing_returns")
    if context.hand_size<=3 and category=="draw":
        score+=19
        factors.append("low_hand_refill")
    if context.hand_size>=7 and category=="draw":
        score-=13
        factors.append("hand_near_cleanup")
    if context.life<=15 and category=="removal" and context.opposing_creatures:
        score+=18
        factors.append("defensive_removal")
    if context.life<=10 and category=="reanimate":
        score+=6
        factors.append("rebuild_board")
    if context.graveyard_creatures==0 and category=="reanimate":
        score-=15
        factors.append("few_graveyard_targets")
    if context.friendly_creatures==0 and category=="token":
        score+=6
        factors.append("develop_board")
    # Deck-density observations influence weights but never legal actions.
    if style=="adaptive":
        if signals.dense("spell_engine") and category=="engine":
            score+=14
            factors.append("spell_trigger_density")
        if signals.dense("graveyard") and category=="reanimate":
            score+=10
            factors.append("graveyard_density")
        if signals.dense("tokens") and category=="token":
            score+=9
            factors.append("token_density")
        if signals.dense("sacrifice") and category=="engine":
            score+=6
            factors.append("death_engine_density")
        if signals.dense("artifacts") and category=="ramp":
            score+=3
            factors.append("artifact_density")
        if signals.dense("combat") and category=="creature":
            score+=5
            factors.append("combat_keyword_density")
    bump=_PERSONALITY[style].get(category,0)
    if bump:
        score+=bump
        factors.append("personality:"+style)
    return RankedChoice(score,category,tuple(factors))


def choose_legal_option(options,context,signals,catalog,*,style="adaptive"):
    """Order the current runner's tuples, never produce a fabricated action.

    The driver tuple is (legacy_priority,paid_sources,name,physical_id,kind,
    cost,target). Selection is deterministic across Python versions,
    unaffected by randomized set iteration or commander names.
    """
    if not options:
        return None,None
    scored=[]
    for option in options:
        if len(option)!=7:
            raise ValueError("Unexpected typed driver option")
        _,paid,name,oid,kind,cost,target=option
        if type(oid) is not int or type(paid) is not int:
            raise ValueError("Invalid source-paid option")
        result=rank_legal_action(kind,catalog.get(name,{}),context,signals,
                                 style=style)
        scored.append(((-result.score,paid,name,oid),option,result))
    _,best,result=min(scored,key=lambda item:item[0])
    return best,result


@dataclass(frozen=True)
class CombatPosture:
    """Bounded combat preference; never changes attacker or blocker legality."""
    attack_limit: int
    reserve: int
    factors: tuple[str,...]

    def as_dict(self):
        return {"attack_limit":self.attack_limit,"reserve":self.reserve,
                "factors":list(self.factors)}


def choose_combat_posture(*,life,opposing_creatures,style="adaptive",signals=None):
    """Choose aggression from public board pressure and the same pilot style.

    The physical kernel still selects legal attackers/blocks and resolves
    damage. These settings only cap optional attackers and defensive reserves;
    they are not predictions of unmodeled combat rules or card permissions.
    """
    if style not in STYLES:
        raise ValueError("Unknown combat pilot personality")
    if (type(life) is not int or type(opposing_creatures) is not int
            or opposing_creatures<0):
        raise ValueError("Invalid combat pilot context")
    if signals is not None and not isinstance(signals,DeckSignals):
        raise TypeError("Verified deck signals required")
    reserve=(2 if life<=18 and opposing_creatures>=5 else
             1 if opposing_creatures>=5 else 0)
    limit=3
    factors=["base:board_pressure"]
    if style=="tempo":
        reserve=max(0,reserve-1)
        limit=4
        factors.append("personality:tempo")
    elif style=="conservative":
        limit=2
        if opposing_creatures:
            reserve=min(3,reserve+1)
        factors.append("personality:conservative")
    elif (style=="engine" and opposing_creatures
          and signals is not None
          and (signals.dense("spell_engine") or signals.dense("sacrifice"))):
        reserve=min(3,reserve+1)
        factors.append("protect_engine_development")
    elif (style=="adaptive" and signals is not None
          and signals.dense("combat")):
        reserve=max(0,reserve-1)
        limit=4
        factors.append("deck_combat_density")
    return CombatPosture(limit,reserve,tuple(factors))
