"""Conservative import-time provisional rules for *any* pinned Commander deck.

This classifier is an optional on-ramp, never a replacement for source-reviewed
rules. It recognizes a small, exact grammar of low-ambiguity ordinary bodies,
tap-mana sources, and one-step spells from *pinned* Scryfall facts; other
abilities stay unimplemented and visible to users. No card-name allowlist.
Every provisional action must still use the real kernel, legal paid sources
and ordinary zones; no action may be claimed fully Oracle-exact by inference.
"""
from dataclasses import dataclass
import re

from .effect_templates import ManaMode
from .mana_costs import UnsupportedManaCost, parse_fixed_mana_cost

_WORDS = {"a":1, "one":1, "two":2, "three":3, "four":4,
          "five":5, "six":6, "seven":7}
_MANA = re.compile(r"^\{T\}: Add ((?:\{[WUBRGC]\}){1,5})\.$")
_MANA_CHOICE = re.compile(r"^\{T\}: Add \{([WUBRGC])\} or \{([WUBRGC])\}\.$")
_MANA_FUNDED = re.compile(r"^\{([1-5])\}, \{T\}: Add ((?:\{[WUBRGC]\}){1,5})\.$")
_MANA_ANY_COLOR = "{T}: Add one mana of any color."
_MANA_COMMANDER = "{T}: Add one mana of any color in your commander's color identity."


def _parse_mana_line(line):
    """Recognize only self-contained printed activations, never extra clauses.

    Commander-identity output is deferred to the actual deck's identity;
    an identity-dependent profile alone cannot grant unrestricted colors.
    """
    if match := _MANA.fullmatch(line):
        return ((ManaMode(tuple(re.findall(r"\{([WUBRGC])\}", match.group(1)))),), False)
    if match := _MANA_CHOICE.fullmatch(line):
        return (tuple(ManaMode((c,)) for c in dict.fromkeys(match.groups())), False)
    if match := _MANA_FUNDED.fullmatch(line):
        return ((ManaMode(tuple(re.findall(r"\{([WUBRGC])\}", match.group(2))),
                          activation_generic=int(match.group(1))),), False)
    if line == _MANA_ANY_COLOR:
        return (tuple(ManaMode((c,)) for c in "WUBRG"), False)
    if line == _MANA_COMMANDER:
        return ((), True)
    return None
_RESTRICT = re.compile(
    r"\b(as an additional cost|additional cost to cast|"
    r"this spell costs|you (?:can't|cannot|may not) cast|"
    r"cast (?:this|only)|you may cast this|"
    r"if you cast|rather than pay|"
    r"without paying its mana cost|"
    r"unless you pay|affinity for|"
    r"convoke|delve|improvise|evoke|"
    r"prototype|mutate|bestow|impending)\b", re.I)
_ENTRY = re.compile(r"\b(?:enter|enters|entering)\b", re.I)
_DRAW_LOSE = re.compile(
    r"^You draw (a|one|two|three|four|five|six|seven|\d+) cards?"
    r" and lose (\d+) life\.$", re.I)
_DRAW = re.compile(
    r"^(?:You )?[Dd]raw (a|one|two|three|four|five|six|seven|\d+) cards?\.$")
_GAIN = re.compile(r"^You gain (\d+) life\.$")
_DRAIN = re.compile(r"^Each opponent loses (\d+) life\.$")
_CREATURE_TOKENS = re.compile(
    r"^Create (a|one|two|three|four|five|six|seven|\d+) "
    r"(tapped )?(\d+)/(\d+) "
    r"(white|blue|black|red|green|colorless) "
    r"([A-Z][A-Za-z'-]+) creature tokens?\.$")
_COLOR_CODES={"white":"W","blue":"U","black":"B","red":"R",
              "green":"G","colorless":""}
_TYPES = frozenset({"land","creature","artifact","enchantment","instant","sorcery"})


@dataclass(frozen=True)
class ProvisionalProfile:
    oracle_id: str
    oracle_text: str
    mana_cost: str
    kind: str  # creature_body, artifact_body, land_mana, artifact_mana, simple_spell
    mode: str = ""
    amount: int = 0
    life_amount: int = 0
    mana_modes: tuple[ManaMode,...] = ()
    commander_identity_mana: bool = False
    enter_tapped: bool = False
    token_power: int = 0
    token_toughness: int = 0
    token_color: str = ""
    token_subtype: str = ""
    token_tapped: bool = False
    omissions: tuple[str,...] = ()
    fidelity: str = "provisional_partial"
    def __post_init__(self):
        if (not self.oracle_id or not isinstance(self.oracle_text,str)
                or self.kind not in {"creature_body","artifact_body",
                                    "land_mana","artifact_mana","simple_spell"}
                or self.fidelity!="provisional_partial"
                or self.amount<0 or self.life_amount<0
                or self.token_power<0 or self.token_toughness<0
                or self.token_color not in {"","W","U","B","R","G"}
                or type(self.commander_identity_mana) is not bool
                or (self.commander_identity_mana
                    and self.kind not in {"land_mana","artifact_mana"})
                or type(self.token_tapped) is not bool):
            raise ValueError("Invalid provisional source descriptor")


def provisional_profile(raw):
    """Return a typed, *partial* profile or None, using exact pinned fields.

    For new cards this may authorize a basic physical body or mana/draw
    subeffect; it never authorizes a complex printed spell to silently
    resolve with missing mandatory actions. Multi-face layouts fail closed.
    """
    if (not isinstance(raw,dict) or raw.get("layout")!="normal"
            or not isinstance(raw.get("oracle_id"),str)
            or not raw["oracle_id"]
            or not isinstance(raw.get("oracle_text"),str)
            or not isinstance(raw.get("type_line"),str)):
        return None
    text=raw["oracle_text"].strip()
    head=raw["type_line"].split(" — ",1)[0].lower().split()
    types=frozenset(head)&_TYPES
    if len(types.intersection({"instant","sorcery"}))==1 and len(types)==1:
        mana=raw.get("mana_cost")
        if not isinstance(mana,str) or not mana:
            return None
        try:parse_fixed_mana_cost(mana)
        except UnsupportedManaCost:return None
        if match:=_DRAW_LOSE.fullmatch(text):
            amount=_WORDS.get(match.group(1).lower())
            if amount is None:
                amount=int(match.group(1))
            loss=int(match.group(2))
            if 1<=amount<=7 and 1<=loss<=20:
                return ProvisionalProfile(raw["oracle_id"],raw["oracle_text"],
                    mana,"simple_spell","draw_lose",amount,loss,
                    omissions=("No opposing priority or counterspell response",))
        if match:=_DRAW.fullmatch(text):
            amount=_WORDS.get(match.group(1).lower())
            if amount is None:amount=int(match.group(1))
            if 1<=amount<=7:
                return ProvisionalProfile(raw["oracle_id"],raw["oracle_text"],
                    mana,"simple_spell","draw",amount,
                    omissions=("No opposing priority or counterspell response",))
        if match:=_CREATURE_TOKENS.fullmatch(text):
            count=_WORDS.get(match.group(1).lower())
            if count is None:count=int(match.group(1))
            power,toughness=int(match.group(3)),int(match.group(4))
            if 1<=count<=20 and 0<=power<=15 and 0<=toughness<=15:
                return ProvisionalProfile(
                    raw["oracle_id"],raw["oracle_text"],mana,
                    "simple_spell","create_creature_tokens",count,
                    token_power=power,token_toughness=toughness,
                    token_color=_COLOR_CODES[match.group(5)],
                    token_subtype=match.group(6),
                    token_tapped=bool(match.group(2)),
                    omissions=("No opposing priority or counterspell response",))
        if match:=_GAIN.fullmatch(text):
            amount=int(match.group(1))
            if 1<=amount<=20:
                return ProvisionalProfile(raw["oracle_id"],raw["oracle_text"],
                    mana,"simple_spell","gain_life",amount,
                    omissions=("No opposing priority or counterspell response",))
        if match:=_DRAIN.fullmatch(text):
            amount=int(match.group(1))
            if 1<=amount<=20:
                return ProvisionalProfile(raw["oracle_id"],raw["oracle_text"],
                    mana,"simple_spell","opponent_loss",amount,
                    omissions=("No opposing priority or counterspell response",))
        return None

    if not types or "instant" in types or "sorcery" in types:
        return None
    if "land" in types and len(types)>1:
        return None
    mana_cost=raw.get("mana_cost") or ""
    if "land" not in types:
        try:parse_fixed_mana_cost(mana_cost)
        except UnsupportedManaCost:return None
    # Modal/replacement entry, alternative costs, and spell restrictions
    # cannot be reduced safely to a body or a mana ability. Do not smuggle
    # mandatory enter effects into a provisional body cast.
    remainder=text
    entry_tapped=False
    if "land" in types or "artifact" in types:
        tapped_line=(r"This (?:land|artifact) enters tapped\.")
        if re.search(r"(?m)^"+tapped_line+r"$",remainder):
            remainder=re.sub(r"(?m)^"+tapped_line+r"\n?","",remainder).strip()
            entry_tapped=True
    if _ENTRY.search(remainder) or _RESTRICT.search(remainder):
        return None

    if types==frozenset({"land"}) or "artifact" in types:
        mana_modes=[]
        commander_identity_mana=False
        ignored=[]
        for line in remainder.splitlines():
            parsed=_parse_mana_line(line.strip())
            if parsed is None:
                ignored.append(line)
                continue
            modes,uses_identity=parsed
            mana_modes.extend(modes)
            commander_identity_mana |= uses_identity
        # This is an ability-level fallback; other optional printed abilities
        # remain omissions. Mandatory entry/casting restrictions have already
        # failed closed above.
        if (mana_modes or commander_identity_mana) and len(mana_modes)<=8:
            kind="land_mana" if "land" in types else "artifact_mana"
            return ProvisionalProfile(raw["oracle_id"],raw["oracle_text"],
                    mana_cost,kind,
                    mana_modes=tuple(dict.fromkeys(mana_modes)),
                    commander_identity_mana=commander_identity_mana,
                    enter_tapped=entry_tapped,
                    omissions=("Additional printed abilities not executed",)
                              +tuple(ignored) if ignored else
                              ("Only source-paid tap-for-mana modes implemented",))
    # Generic creature enters as a real physical body. Printed keyword
    # characteristics are read from pinned card faces by the loader.
    if "creature" in types:
        return ProvisionalProfile(raw["oracle_id"],raw["oracle_text"],
                    mana_cost,"creature_body",
                    omissions=("Non-keyword abilities unreviewed; no automatic "
                               "enter/death/combat/activation effects",))
    if types==frozenset({"artifact"}):
        return ProvisionalProfile(raw["oracle_id"],raw["oracle_text"],
                    mana_cost,"artifact_body",
                    enter_tapped=entry_tapped,
                    omissions=("Non-mana artifact abilities unreviewed",))
    return None


def provisional_report(entries):
    """Import-time preview, suitable for UI badges and review prioritization.

    Does not change a deck or upgrade a card to fully reviewed.
    """
    result=[]
    for entry in entries:
        raw=entry.get("card") if isinstance(entry,dict) else None
        profile=provisional_profile(raw)
        name=entry.get("deck_name") if isinstance(entry,dict) else None
        result.append({"card":name or (raw or {}).get("name"),
                       "oracle_id":(raw or {}).get("oracle_id"),
                       "status":"provisional" if profile else "manual_review_needed",
                       "kind":profile.kind if profile else None,
                       "mode":profile.mode if profile else None,
                       "fidelity":profile.fidelity if profile else "unsupported",
                       "omissions":list(profile.omissions) if profile else []})
    return result
