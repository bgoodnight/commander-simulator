"""Declare attacks/blocks first, then one simultaneous ordinary damage batch.

One blocker per attacker is the supported assignment subset. No first/double
strike, trample, banding or planeswalker/battle attacks are inferred.
"""
from dataclasses import dataclass, field
from rules import Event
import simulation as base
import integrated as v6

@dataclass
class Attack:
    attacker: int
    defender: int
    blocked: bool = False
    blockers: list[int] = field(default_factory=list)


class Combat:
    def __init__(self, table): self.t = table; self.attacks = []

    def eligible(self, player):
        t = self.t
        return tuple(c for c in player.creatures if not t.rules.get(c.id).tapped
                     and (c.id in t.attack_ready.get(player.seat, ()) or 'haste' in t.rules.get(c.id).keywords))

    def declare_attackers(self, player, selection=None):
        t = self.t; legal = {c.id: c for c in self.eligible(player)}
        if selection is None:
            selected = []
            for c in legal.values():
                rate = base.CONF['attack_rate'].get(player.archetype, .65)
                if player is t.details and c.name == 'Magnus the Red': rate = .78
                if player is t.details and c.name in v6.ENGINE_BODIES: continue
                if player.rng.random() >= rate: continue
                target = t.choose_target(player, 'attack')
                if target: selected.append((c.id, target.seat))
        else: selected = list(selection)
        if len({oid for oid, _ in selected}) != len(selected): raise ValueError('Attacker declared twice')
        if any(oid not in legal or seat == player.seat or seat not in range(4) or not t.players[seat].alive
               for oid, seat in selected): raise ValueError('Illegal attacker declaration')
        self.attacks = [Attack(oid, seat) for oid, seat in selected]
        for attack in self.attacks:
            c = legal[attack.attacker]
            if 'vigilance' not in t.rules.get(c.id).keywords: t.world.tap(c)
            t.emit('combat_attack', attacker=player.seat, defender=attack.defender, creature_id=c.id)
            t.counts['attackers'] += 1
            t.note(f'    ATTACK: P{player.seat} {c.name} #{c.id} -> P{attack.defender}.')
        return tuple(self.attacks)

    def declare_blockers(self, selection=None):
        t = self.t; used = set(); proposed = []
        if selection is None:
            for attack in self.attacks:
                if attack.attacker not in t.rules.objects or not t.players[attack.defender].alive: continue
                attacker = next(c for p in t.players for c in p.creatures if c.id == attack.attacker)
                blocker = t.block(t.players[attack.defender], attacker, used)
                if blocker: proposed.append((attack.attacker, blocker.id)); used.add(blocker.id)
        else: proposed = list(selection)
        used.clear(); seen_attackers = set()
        for attacker, blocker in proposed:
            attack = next((a for a in self.attacks if a.attacker == attacker), None)
            if attack is None or attacker not in t.rules.objects or blocker in used or attacker in seen_attackers:
                raise ValueError('Illegal or unsupported multiple-block assignment')
            legal = {o.object_id for o in t.rules.legal_blockers(attacker, attack.defender)}
            if blocker not in legal: raise ValueError('Illegal blocker')
            used.add(blocker); seen_attackers.add(attacker)
        for attacker, blocker in proposed:
            attack = next(a for a in self.attacks if a.attacker == attacker)
            attack.blocked = True; attack.blockers = [blocker]
            t.counts['blocks'] += 1
            t.note(f'    BLOCK: #{blocker} blocks #{attacker}.')
        return tuple(self.attacks)

    def damage(self, player):
        t = self.t; creatures = {}; players = {}; dealt = []
        for attack in self.attacks:
            if attack.attacker not in t.rules.objects or not t.players[attack.defender].alive: continue
            attacker = t.rules.get(attack.attacker)
            if attacker.zone != 'battlefield' or attacker.controller != player.seat or 'creature' not in attacker.types: continue
            blockers = [t.rules.get(oid) for oid in attack.blockers if oid in t.rules.objects
                        and t.rules.get(oid).zone == 'battlefield'
                        and t.rules.get(oid).controller == attack.defender
                        and 'creature' in t.rules.get(oid).types]
            if attack.blocked:
                if blockers:
                    blocker = blockers[0]
                    creatures[blocker.object_id] = creatures.get(blocker.object_id, 0) + max(0, attacker.power)
                    creatures[attacker.object_id] = creatures.get(attacker.object_id, 0) + max(0, blocker.power)
                else:
                    t.note(f'    BLOCKED: #{attacker.object_id} has no remaining blocker; no player damage.')
            else:
                amount = max(0, attacker.power)
                players[attack.defender] = players.get(attack.defender, 0) + amount
                dealt.append((attacker.object_id, attack.defender, amount))
        # Mark every creature and change every player's life BEFORE the SBA window.
        for oid, amount in creatures.items():
            t.rules.get(oid).damage_marked += amount
            t.rules.events.append(Event('damage_creature', player.seat, target_id=oid, amount=amount))
        lives = {p.seat: p.life for p in t.players}
        result = t.rules.damage_players(lives, players, player.seat)
        for seat, amount in players.items():
            target = t.players[seat]; target.life = lives[seat]; target.damage_taken += amount
            player.damage_dealt += amount
            t.emit('damage', source=player.seat, target=seat, amount=amount, cause='combat')
        if len(result.eliminated) > 1: t.counts['multi_elimination_events'] += 1
        for oid, seat, amount in dealt:
            if amount:
                t._apply_pending(t.rules.triggers(Event('combat_damage_player', player.seat, oid, amount=amount)))
        t.rules._dirty()
        record = {'attackers': [(a.attacker, a.defender, a.blocked, list(a.blockers)) for a in self.attacks],
                  'creature_damage': creatures, 'player_damage': players}
        t.combat_batches.append(record)
        t.note(f'    COMBAT DAMAGE simultaneous: creatures={creatures}; players={players}.')
        return record
