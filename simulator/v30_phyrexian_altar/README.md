# V30 Phyrexian Altar subset

`AltarTable` supports casting Phyrexian Altar for three generic mana. Its immediate mana ability sacrifices one controlled creature and produces one blue or red mana; the artifact does not tap and may be activated repeatedly. Tapped and newly controlled creatures are valid sacrifices. The mana planner prefers tokens to other creatures where other factors are equal. Mana abilities resolve immediately and do not use the stack. Proxy status has no effect on simulation.

This is partial: the existing pool cannot represent white, black or green, although the printed card can produce any color. Automatic planning does not currently use a creature's own tap-mana ability and then sacrifice that same creature in one payment; nor does it sacrifice an Altar that has become a creature. Sacrifice and death triggers are not generally implemented, and the simulator does not yet model convoke/Altar coordination. Mana plan caches predate this milestone; no new caching was added. The coverage audit records this card as partial.

See the source-paid interaction report in this folder and the [Oracle card identity snapshot](../v20_verified_types/CARD_IDENTITIES.json).
