"""Immutable offline Scryfall identities shared across multiple decklists.

No network calls occur in this module. Printed identity data does not imply
effect/rules coverage. Each Oracle ID can have multiple immutable revisions;
a deck manifest pins the selected revision for deterministic replay.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

SCHEMA_VERSION = 1


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp",
                                    dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def deck_names(deck_bytes):
    """Collect names from a sectioned decklist, not headings/comments."""
    names = []
    for line in deck_bytes.decode("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([1-9]\d*) (\S(?:.*\S)?)", line)
        if match:
            names.append(match[2])
    if not names:
        raise ValueError("No card entries in decklist")
    return list(dict.fromkeys(names))


def card_aliases(card):
    aliases = {card["name"]}
    faces = card.get("card_faces", [])
    if faces:
        aliases.update(face["name"] for face in faces)
        if len(faces) > 1:
            aliases.add(" // ".join(face["name"] for face in faces))
    return aliases


def verify_card(card):
    """Reject missing identity/characteristics before admitting cache data."""
    if not isinstance(card, dict):
        raise ValueError("Expected a Scryfall card record")
    identity = card.get("oracle_id")
    name = card.get("name")
    if not isinstance(identity, str) or not identity.strip():
        raise ValueError("Missing Oracle ID")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Missing card name")
    if not isinstance(card.get("type_line"), str) or not card["type_line"]:
        raise ValueError("Missing card type")
    if not isinstance(card.get("cmc"), (int, float)) or isinstance(card["cmc"], bool):
        raise ValueError("Missing mana value")
    if not isinstance(card.get("keywords"), list):
        raise ValueError("Missing printed keywords")
    if not isinstance(card.get("color_identity"), list) or any(
        value not in "WUBRG" or len(value) != 1 for value in card["color_identity"]
    ):
        raise ValueError("Invalid color identity")
    if not isinstance(card.get("layout"), str) or not card["layout"]:
        raise ValueError("Missing layout")
    if not isinstance(card.get("scryfall_uri"), str) or not card["scryfall_uri"]:
        raise ValueError("Missing Scryfall source")
    faces = card.get("card_faces", [])
    if not isinstance(faces, list) or any(
        not isinstance(f, dict) or not isinstance(f.get("name"), str) or not f["name"]
        for f in faces
    ):
        raise ValueError("Invalid card faces")
    return identity


class CardCatalog:
    """Locally cached revisions; mutable only during explicit import/refresh."""

    def __init__(self, path):
        self.path = Path(path)
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            data = {"schema_version": SCHEMA_VERSION, "revisions": {}, "current": {}}
        if (not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION
            or not isinstance(data.get("revisions"), dict)
            or not isinstance(data.get("current"), dict)):
            raise ValueError("Invalid shared catalog schema")
        self.revisions = data["revisions"]
        self.current = data["current"]
        self._aliases = {}
        for oracle_id, versions in self.revisions.items():
            if not isinstance(versions, dict):
                raise ValueError("Invalid catalog revision mapping")
            for sha, card in versions.items():
                if verify_card(card) != oracle_id or digest(card) != sha:
                    raise ValueError("Corrupt catalog card revision: " + oracle_id)
        for oracle_id, revision in self.current.items():
            if oracle_id not in self.revisions or revision not in self.revisions[oracle_id]:
                raise ValueError("Current catalog revision is missing")
        self._build_aliases()

    def _build_aliases(self):
        self._aliases = {}
        for oracle_id, revision in self.current.items():
            card = self.revisions[oracle_id][revision]
            for name in card_aliases(card):
                old = self._aliases.setdefault(name, oracle_id)
                if old != oracle_id:
                    raise ValueError("Ambiguous cached card alias: " + name)

    def lookup(self, name):
        """An exact card/face alias; never guess identity from a prefix."""
        oracle_id = self._aliases.get(name)
        if oracle_id is None:
            return None
        sha = self.current[oracle_id]
        return oracle_id, sha, self.revisions[oracle_id][sha]

    def add_card(self, card):
        oracle_id = verify_card(card)
        sha = digest(card)
        self.revisions.setdefault(oracle_id, {})[sha] = card
        self.current[oracle_id] = sha
        self._build_aliases()
        return oracle_id, sha

    def seed_snapshot(self, snapshot_path, *, deck_path=None):
        """Explicitly seed from a trusted existing snapshot, with optional hash check."""
        data = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
        if (data.get("problems") or not str(data.get("source", "")).startswith("Scryfall")
            or not data.get("retrieved_at") or not data.get("deck_sha256")):
            raise ValueError("Untrusted or incomplete seed snapshot")
        entries = data.get("cards")
        if not isinstance(entries, list) or len(entries) != data.get("distinct_requested"):
            raise ValueError("Invalid seed snapshot count")
        if deck_path is not None:
            deck_bytes = Path(deck_path).read_bytes()
            if hashlib.sha256(deck_bytes).hexdigest() != data["deck_sha256"]:
                raise ValueError("Seed snapshot deck hash mismatch")
            if set(deck_names(deck_bytes)) != {item["deck_name"] for item in entries}:
                raise ValueError("Seed snapshot name set mismatch")
        for entry in entries:
            if (not isinstance(entry, dict) or not isinstance(entry.get("deck_name"), str)
                or entry["deck_name"] not in card_aliases(entry["card"])):
                raise ValueError("Unmatched seed card name")
            self.add_card(entry["card"])

    def get_pinned(self, oracle_id, revision):
        try:
            return self.revisions[oracle_id][revision]
        except KeyError as exc:
            raise ValueError("Missing pinned card revision: " + oracle_id) from exc

    def save(self):
        # Preserve every older immutable revision referenced by saved manifests.
        self._build_aliases()
        atomic_json(self.path, {"schema_version": SCHEMA_VERSION,
                                "revisions": self.revisions, "current": self.current})


def pinned_deck_entries(deck_path, manifest_path, catalog_path):
    """Read a pinned deck manifest without making any API request."""
    raw = Path(deck_path).read_bytes()
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if (manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("deck_sha256") != hashlib.sha256(raw).hexdigest()):
        raise ValueError("Manifest does not match the deck file")
    expected = deck_names(raw)
    entries = manifest.get("cards")
    if not isinstance(entries, list) or [e.get("deck_name") for e in entries] != expected:
        raise ValueError("Manifest card names do not match deck")
    catalog = CardCatalog(catalog_path)
    resolved = []
    for entry in entries:
        card = catalog.get_pinned(entry["oracle_id"], entry["revision"])
        if entry["deck_name"] not in card_aliases(card):
            raise ValueError("Manifest card identity mismatch")
        resolved.append({"deck_name": entry["deck_name"], "card": card})
    return resolved
