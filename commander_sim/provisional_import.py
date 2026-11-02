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
from .library_actions import LibraryAction, required_draws
from .death_recipes import provisional_death_recipe
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
    r"unless you pay|spend (?:this|that) mana only|activate only|"
    r"affinity for|"
    r"convoke|delve|improvise|evoke|"
    r"prototype|mutate|bestow|impending)\b", re.I)
_ENTRY = re.compile(r"\b(?:enter|enters|entering)\b", re.I)
_DRAW_LOSE = re.compile(
    r"^You draw (a|one|two|three|four|five|six|seven|\d+) cards?"
    r" and lose (\d+) life\.$", re.I)
_DRAW = re.compile(
    r"^(?:You )?[Dd]raw (a|one|two|three|four|five|six|seven|\d+) cards?\.$")
_GAIN = re.compile(r"^You gain (\d+) life\.$")
_SCRY_DRAW = re.compile(
    r"^Scry ([1-3]), then draw (a|one|two|three|\d+) cards?\.$", re.I)
_SURVEIL_DRAW = re.compile(
    r"^Surveil ([1-3])\.\nDraw (a|one|two|three|\d+) cards?\.$", re.I)
_DRAW_DISCARD = re.compile(
    r"^Draw (a|one|two|three|four|five|\d+) cards?, then "
    r"discard (a|one|two|three|four|five|\d+) cards?\.$", re.I)
_SCRY_ONLY = re.compile(r"^Scry ([1-3])\.$", re.I)
_SURVEIL_ONLY = re.compile(r"^Surveil ([1-3])\.$", re.I)
_MILL_ONLY = re.compile(r"^(?:You )?[Mm]ill (a|one|two|three|four|five|six|seven|\d+) cards?\.$")
_ENTRY_MILL = re.compile(
    r"^When this creature enters, mill (a|one|two|three|four|five|six|seven|\d+) cards?\.$")
_ENTRY_DRAW = re.compile(
    r"^(?:[A-Za-z][A-Za-z '’\-]{1,55} — )?"
    r"When this creature enters, draw "
    r"(a|one|two|three|four|five|six|seven|\d+) cards?\.$")
_ENTRY_MILL_DRAW = re.compile(
    r"^(?:[A-Za-z][A-Za-z '’\-]{1,55} — )?"
    r"When this creature enters, mill "
    r"(a|one|two|three|four|five|six|seven|\d+) cards?, then draw "
    r"(a|one|two|three|four|five|six|seven|\d+) cards?\.$")
_ENTRY_DRAW_DISCARD = re.compile(
    r"^(?:[A-Za-z][A-Za-z '’\-]{1,55} — )?"
    r"When this creature enters, draw "
    r"(a|one|two|three|four|five|six|seven|\d+) cards?, then discard "
    r"(a|one|two|three|four|five|six|seven|\d+) cards?\.$")


def _quantity(word):
    return _WORDS.get(word.lower(), int(word) if word.isdigit() else 0)


def _library_recipe(text):
    """Parse only complete, stand-alone simple library sentences.

    Reminder text, alternate costs and trailing clauses fail closed. More
    complex official cards use exact reviewed registrations instead.
    """
    if match := _SCRY_DRAW.fullmatch(text):
        draw = _quantity(match.group(2))
        return (LibraryAction("scry", int(match.group(1))),
                LibraryAction("draw", draw)) if 1 <= draw <= 7 else ()
    if match := _SURVEIL_DRAW.fullmatch(text):
        draw = _quantity(match.group(2))
        return (LibraryAction("surveil", int(match.group(1))),
                LibraryAction("draw", draw)) if 1 <= draw <= 7 else ()
    if match := _DRAW_DISCARD.fullmatch(text):
        draw, discard = (_quantity(x) for x in match.groups())
        if 1 <= draw <= 7 and 1 <= discard <= 7:
            return (LibraryAction("draw", draw),
                    LibraryAction("discard", discard))
    if match := _SCRY_ONLY.fullmatch(text):
        return (LibraryAction("scry", int(match.group(1))),)
    if match := _SURVEIL_ONLY.fullmatch(text):
        return (LibraryAction("surveil", int(match.group(1))),)
    if match := _MILL_ONLY.fullmatch(text):
        count=_quantity(match.group(1))
        return (LibraryAction("mill",count),) if 1<=count<=7 else ()
    return ()

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
    library_actions: tuple[LibraryAction,...] = ()
    entry_actions: tuple[LibraryAction,...] = ()
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
                or type(self.token_tapped) is not bool
                or not isinstance(self.library_actions, tuple)
                or not all(isinstance(x, LibraryAction)
                           for x in self.library_actions)
                or (self.library_actions and self.kind != "simple_spell")
                or not isinstance(self.entry_actions,tuple)
                or not all(isinstance(x,LibraryAction)
                           and x.kind in {"mill","draw","discard"}
                           for x in self.entry_actions)
                or (self.entry_actions and self.kind!="creature_body")):
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
        if actions := _library_recipe(text):
            return ProvisionalProfile(
                raw["oracle_id"], raw["oracle_text"], mana,
                "simple_spell", "library_sequence", required_draws(actions),
                library_actions=actions,
                omissions=("Library selection uses bounded deterministic policy",
                           "No opposing priority or counterspell response"))
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
    entry_actions=()
    if "creature" in types:
        # Compose only exact, complete mandatory entry sentences. Named
        # ability labels may precede the printed entry-draw line. Any
        # unrecognized extra enters/replacement clause still fails closed.
        remainder_lines=[]
        accepted=[]
        for line in remainder.splitlines():
            stripped=line.strip()
            compound=_ENTRY_MILL_DRAW.fullmatch(stripped)
            if compound is not None:
                mill,draw=(_quantity(word) for word in compound.groups())
                if not (1<=mill<=7 and 1<=draw<=7):
                    return None
                accepted.extend((LibraryAction("mill",mill),
                                 LibraryAction("draw",draw)))
                continue
            compound=_ENTRY_DRAW_DISCARD.fullmatch(stripped)
            if compound is not None:
                draw,discard=(_quantity(word) for word in compound.groups())
                if not (1<=draw<=7 and 1<=discard<=draw):
                    return None
                accepted.extend((LibraryAction("draw",draw),
                                 LibraryAction("discard",discard)))
                continue
            match=_ENTRY_MILL.fullmatch(stripped)
            kind="mill" if match is not None else None
            if match is None:
                match=_ENTRY_DRAW.fullmatch(stripped)
                kind="draw" if match is not None else None
            if match is None:
                remainder_lines.append(line)
                continue
            count=_quantity(match.group(1))
            if not 1<=count<=7:
                return None
            accepted.append(LibraryAction(kind,count))
        if len(accepted)>3:
            return None
        entry_actions=tuple(accepted)
        remainder="\n".join(remainder_lines).strip()
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
                    mana_cost,"creature_body",entry_actions=entry_actions,
                    omissions=(("Provisional grammar only for exact entry library actions",
                                "Other printed abilities remain unreviewed",
                                "No opposing priority or counterspell response")
                               if entry_actions else
                               ("Non-keyword abilities remain unreviewed; only "
                                "separately recognized simple triggers execute",)))
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
        death=(provisional_death_recipe(raw.get("oracle_text", ""))
               if profile is not None and profile.kind=="creature_body"
               else None)
        name=entry.get("deck_name") if isinstance(entry,dict) else None
        result.append({"card":name or (raw or {}).get("name"),
                       "oracle_id":(raw or {}).get("oracle_id"),
                       "status":"provisional" if profile else "manual_review_needed",
                       "kind":profile.kind if profile else None,
                       "mode":profile.mode if profile else None,
                       "actions":[{"kind":x.kind,"count":x.count}
                                  for x in profile.library_actions]
                                  if profile else [],
                       "entry_actions":[{"kind":x.kind,"count":x.count}
                                        for x in profile.entry_actions]
                                        if profile else [],
                       "provisional_death_trigger":(
                           {"scope":{"relation":death.predicate.relation,
                                     "types":sorted(death.predicate.types_any),
                                     "subtype":death.predicate.subtype,
                                     "non_token":death.predicate.nontoken_only,
                                     "exclude_source":death.predicate.exclude_source},
                            "steps":[{"kind":x.kind,"count":x.count}
                                     for x in death.steps]}
                           if death else None),
                       "fidelity":profile.fidelity if profile else "unsupported",
                       "omissions":list(profile.omissions) if profile else []})
    return result
