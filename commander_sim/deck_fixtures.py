"""Authoritative named deck variants for offline M1 import and observation.

These paths are fixtures, not ownership proof or executable game rules.
Import uses a single cache catalog but pins every deck's own card revisions.
"""
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_DATA = ROOT / "simulator" / "card_data"
SHARED_CATALOG = CARD_DATA / "shared_scryfall_catalog.json"


@dataclass(frozen=True)
class DeckFixture:
    key: str
    commander: str
    relative_path: str
    status: str

    @property
    def deck_path(self):
        return ROOT / self.relative_path

    @property
    def snapshot_path(self):
        return CARD_DATA / f"{self.key}_m1_scryfall.json"

    @property
    def manifest_path(self):
        return self.snapshot_path.with_suffix(".manifest.json")


FIXTURES = (
    DeckFixture("magnus_premium", "Magnus the Red",
                "decklists/magnus_thousand_sons_v1_14_premium.txt", "ideal"),
    DeckFixture("magnus_budget", "Magnus the Red",
                "decklists/magnus_thousand_sons_v1_13_budget.txt", "budget"),
    DeckFixture("wretched_ranks", "Ghoulcaller Gisa",
                "decklists/wretched_ranks_foundations_precon_2026.txt", "owned_precon"),
    DeckFixture("mortarion_current", "Mortarion, Daemon Primarch",
                "decklists/mortarion_current_ordered_plus_owned_2026_10_31.txt", "ordered_plus_owned"),
    DeckFixture("mortarion_ideal", "Mortarion, Daemon Primarch",
                "decklists/mortarion_inexorable_plague_host_ideal.txt", "ideal"),
    DeckFixture("necron_dynasties", "Szarekh, the Silent King",
                "decklists/necron_dynasties_warhammer_40k_precon.txt", "owned_precon"),
)

LEGACY_SEEDS = (
    ("decklists/fixtures/magnus_flameslinger_v0_7_pre_delivery.txt",
     "simulator/card_data/flameslinger_v0_7_scryfall.json"),
    ("decklists/wretched_ranks_foundations_precon_2026.txt",
     "simulator/card_data/gisa_scryfall.json"),
    ("decklists/mortarion_purchase_reconciled_candidate_2026_10_27.txt",
     "simulator/card_data/mortarion_scryfall.json"),
)
