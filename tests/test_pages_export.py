"""Static GitHub Pages release gate: no Python backend or unverified results."""
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.build_pages_deck_lab import build, DEFAULT_SEEDS, card_image


class StaticPagesTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.destination=Path(self.temp.name)/"pages"

    def run_build(self, **kwargs):
        with patch("urllib.request.urlopen", side_effect=AssertionError("No network")):
            return build(self.destination, **kwargs)

    def test_verified_and_owned_physical_decks_keep_separate_observation_evidence(self):
        manifest=self.run_build()
        self.assertEqual(manifest["decks"],9)
        self.assertGreater(manifest["cards"],80)
        self.assertGreater(manifest["names"],30000)
        self.assertEqual(manifest["seeds"],list(DEFAULT_SEEDS))
        datasets=json.loads((self.destination/"decks.json").read_text())
        results=json.loads((self.destination/"observations.json").read_text())
        batches=json.loads((self.destination/"bounded-batches.json").read_text())
        # The legacy four-deck cache remains exportable until refreshed.
        approved={d["key"] for d in datasets["decks"]}
        self.assertTrue(set(batches["decks"]).issubset(approved))
        self.assertIn(len(batches["decks"]), (4,6))
        for key in batches["decks"]:
            runs=json.loads((self.destination/f"bounded-runs-{key}.json").read_text())
            self.assertEqual(len(runs),100)
            self.assertEqual({r["seed"] for r in runs},set(range(100)))
        self.assertEqual(datasets["data_mode"],"precomputed_observation_only")
        self.assertEqual(len(datasets["decks"]),9)
        self.assertTrue({"magnus_physical_owned","magnus_physical_trial","mortarion_physical_final"}.issubset(approved))
        owned=next(d for d in datasets["decks"] if d["key"]=="magnus_physical_owned")
        trial=next(d for d in datasets["decks"] if d["key"]=="magnus_physical_trial")
        self.assertEqual(owned["unverified_cards"],["Narset's Rebuke"])
        self.assertEqual(results["magnus_physical_owned"],{})
        self.assertEqual(len(owned["sideboard"]),9)
        self.assertEqual(next(c["qty"] for c in owned["cards"] if c["name"]=="Island"),15)
        self.assertEqual(next(c["qty"] for c in trial["cards"] if c["name"]=="Island"),16)
        self.assertIn("Narset's Rebuke",{c["name"] for c in owned["cards"]})
        self.assertNotIn("Narset's Rebuke",{c["name"] for c in trial["cards"]})
        for deck in datasets["decks"]:
            with self.subTest(deck=deck["key"]):
                # Built-in last-updated is sourced from the committed deck
                # revision, never from a browser clock or Pages deploy date.
                self.assertRegex(deck["updated_at"],r"^\d{4}-\d{2}-\d{2}T")
                self.assertEqual(deck["card_count"],100)
                self.assertEqual(sum(e["qty"] for e in deck["cards"]),100)
                self.assertIn(deck["commander_id"],datasets["cards"])
                self.assertTrue(set(deck["modeled_rocks"]).issubset({c["oracle_id"] for c in deck["cards"]}))
                if deck["key"]=="magnus_physical_owned":
                    self.assertEqual(results[deck["key"]],{})
                    self.assertIsNone(deck["snapshot_sha256"])
                    continue
                self.assertEqual(set(results[deck["key"]]),set(map(str,DEFAULT_SEEDS)))
                for seed,record in results[deck["key"]].items():
                    self.assertEqual(record["seed"],int(seed))
                    self.assertEqual(record["deck_sha256"],deck["deck_sha256"])
                    self.assertEqual(record["mode"],"observation")
                    self.assertEqual(len(record["trace"]),6)
                    self.assertTrue(all(not t["playable_now"] for t in record["trace"]))

    def test_only_allowlisted_site_data_and_no_workspace_are_exported(self):
        self.run_build()
        permitted={"index.html","summary.html","results.html","editor.html",
                   "app.js","results_insights.js","brackets.js","replay.js","gorge_legacy_adapter.js","gorge_replay.js","insight_explorer.js","insight_catalog.js","game_outcomes.js","style.css","game-changers.json","decks.json",
                   "observations.json","names.json","bounded-batches.json","build-manifest.json",".nojekyll"}
        published=json.loads((self.destination/"bounded-batches.json").read_text())
        permitted.update(f"bounded-runs-{key}.json" for key in published["decks"])
        archive_dir=self.destination/"simulation-data"
        if archive_dir.is_dir():
            permitted.add("simulation-data")
            from tools.publish_simulation_archive import validate_index
            self.assertGreaterEqual(len(validate_index(archive_dir)["releases"]),1)
        replay_dir=self.destination/"replay-data"
        if replay_dir.is_dir():
            permitted.add("replay-data")
            entries=list(replay_dir.iterdir())
            self.assertEqual({p.name for p in entries},{"mortarion-opponent-pressure.v1.json"})
            replay=json.loads(entries[0].read_text(encoding="utf-8"))
            self.assertEqual(replay["format"],"commander-replay-v1")
            self.assertEqual(replay["schema_version"],1)
            built_deck=next(d for d in datasets["decks"] if d["key"]=="mortarion_physical_final") if "datasets" in locals() else next(
                d for d in json.loads((self.destination/"decks.json").read_text())["decks"]
                if d["key"]=="mortarion_physical_final")
            self.assertEqual(replay["deck_sha256"],built_deck["deck_sha256"])
            self.assertEqual(len(replay["scenarios"]),5)
        long_game_dir=self.destination/"game-outcomes"
        if long_game_dir.is_dir():
            permitted.add("game-outcomes")
            for p in long_game_dir.glob("*.json"):
                self.assertTrue(p.is_file())
        analytics_dir=self.destination/"analytics"
        if analytics_dir.is_dir():
            permitted.add("analytics")
            # Only vetted published JSON reports, never raw observation archives.
            self.assertTrue(list(analytics_dir.glob("*.json")))
            self.assertTrue(all(p.is_file() and p.suffix==".json"
                                for p in analytics_dir.iterdir()))
        gorge_dir=self.destination/"gorge-data"
        if gorge_dir.is_dir():
            permitted.add("gorge-data")
            manifest=json.loads((gorge_dir/"manifest.json").read_text())
            self.assertIn(manifest["schema"],{"gorge-public-replay-manifest-v1",
                                                    "gorge-omniscient-replay-manifest-v1"})
            omniscient=manifest["schema"]=="gorge-omniscient-replay-manifest-v1"
            if omniscient:
                self.assertEqual(manifest["visibility"],"omniscient")
                self.assertIs(manifest["synthetic_simulation_only"],True)
            self.assertEqual({p.name for p in gorge_dir.iterdir()},
                             {"manifest.json"}|{g["file"] for g in manifest["games"]})
            for game in manifest["games"]:
                replay=json.loads((gorge_dir/game["file"]).read_text())
                self.assertEqual(replay["visibility"],
                                 "omniscient" if omniscient else "public_events_only")
                self.assertTrue(replay["snapshots"])
                self.assertEqual([p["life"] for p in replay["snapshots"][0]["players"]],
                                 [40]*4)
                if omniscient:
                    self.assertIs(replay["synthetic_simulation_only"],True)
                    self.assertTrue(all(
                        len(p["zones"]["hand"])==p["hand_count"]
                        for snap in replay["snapshots"] for p in snap["players"]))
                    self.assertTrue(all(
                        len(p["zones"]["library"])==p["library_count"]
                        for snap in replay["snapshots"] for p in snap["players"]))
                else:
                    self.assertFalse(any(
                        "hand" in p["zones"] or "library" in p["zones"]
                        for snap in replay["snapshots"] for p in snap["players"]))
                self.assertFalse(any(k in replay for k in ("log","objects","intents")))
        self.assertEqual({p.name for p in self.destination.iterdir()},permitted)
        self.assertNotIn("shared_scryfall_catalog.json",permitted)
        self.assertFalse(any(p.is_dir() and p.name not in
                             ("simulation-data","replay-data","game-outcomes","analytics","gorge-data")
                             for p in self.destination.iterdir()))
        page=(self.destination/"index.html").read_text()
        script=(self.destination/"app.js").read_text()
        self.assertIn("commander-rail",page)
        self.assertIn("commander-medallion",page)
        self.assertIn("audio-toggle",page)
        self.assertIn("Simulation Results",page)
        self.assertIn("prefers-reduced-motion",(self.destination/"style.css").read_text())
        self.assertIn("observations.json",script)
        self.assertIn("game-changers.json",script)
        self.assertIn("bracket-assessment",page)
        self.assertIn("brackets.js",page)
        self.assertIn("replay.js",page)
        self.assertIn("insight_explorer.js",page)
        self.assertIn("insight_catalog.js",page)
        self.assertIn("game_outcomes.js",page)
        self.assertIn("gorge_legacy_adapter.js",page)
        self.assertTrue((self.destination/"game_outcomes.js").is_file())
        self.assertIn('id="long-game-panel"',page)
        self.assertTrue((self.destination/"insight_explorer.js").is_file())
        self.assertIn("id=\"opponent-replay-panel\"",page)
        self.assertIn("renderReplay",script)
        registry=json.loads((self.destination/"game-changers.json").read_text())
        self.assertEqual(len(registry["names"]),53)
        self.assertIn("Underworld Breach",registry["names"])
        self.assertIn("localStorage",script)
        self.assertNotIn("/api/observation",script)
        self.assertNotIn("eval(",script)

    def test_ui_asset_urls_are_fingerprinted_from_contents(self):
        self.run_build()
        shell=(self.destination/"index.html").read_text(encoding="utf-8")
        for name in ("app.js","results_insights.js","brackets.js","replay.js",
                     "insight_explorer.js","insight_catalog.js","game_outcomes.js",
                     "style.css"):
            digest=hashlib.sha256((self.destination/name).read_bytes()).hexdigest()[:12]
            self.assertIn("./"+name+"?v="+digest+'"',shell)
            self.assertEqual(shell.count("./"+name+"?v="),1)
        for name in ("summary.html","results.html","editor.html"):
            self.assertEqual(shell,(self.destination/name).read_text(encoding="utf-8"))

    def test_default_results_and_separate_shareable_summary_editor_pages(self):
        manifest=self.run_build()
        for name in ("index.html", "summary.html", "results.html", "editor.html"):
            with self.subTest(page=name):
                page=(self.destination/name).read_text(encoding="utf-8")
                self.assertIn('data-page="results"',page)
                self.assertIn('data-page="summary"',page)
                self.assertIn('data-page="editor"',page)
                self.assertIn('id="commander-picker"',page)
                self.assertIn('id="pane-insights"',page)
                self.assertIn('d3@7',page)
                self.assertIn(name,manifest["asset_sha256"])
        js=(self.destination/"app.js").read_text(encoding="utf-8")
        self.assertIn('location.pathname.endsWith("/summary.html")?"summary":"results"',js)
        self.assertIn("function showPage()",js)
        self.assertIn("function renderScrollStory()",js)
        self.assertIn("IntersectionObserver",js)
        self.assertIn("window.d3",js)
        self.assertIn("window.history.replaceState",js)

    def test_results_is_default_and_summary_has_dedicated_url(self):
        self.run_build()
        page=(self.destination/"index.html").read_text()
        app=(self.destination/"app.js").read_text()
        self.assertIn('data-page="results" href="./results.html"',page)
        self.assertIn('data-page="summary" href="./summary.html"',page)
        self.assertIn('location.pathname.endsWith("/summary.html")?"summary":"results"',app)
        self.assertIn('location.pathname.endsWith("/editor.html")?"editor"',app)
        self.assertTrue((self.destination/"results.html").is_file())
        self.assertEqual(
            (self.destination/"index.html").read_bytes(),
            (self.destination/"summary.html").read_bytes()
        )

    def test_compact_commander_picker_and_named_version_workflow(self):
        self.run_build()
        html=(self.destination/"editor.html").read_text(encoding="utf-8")
        script=(self.destination/"app.js").read_text(encoding="utf-8")
        css=(self.destination/"style.css").read_text(encoding="utf-8")
        for needle in ('id="commander-medallion"', 'id="commander-picker"',
                       'id="active-commander"', 'id="active-deck-name"',
                       'id="global-deck-select"', 'id="new-version-button"',
                       'id="save-local"', 'id="draft-title"'):
            self.assertIn(needle,html)
        for needle in ("latestSelectionForCommander", "loadDeckSelection",
                       "renderDeckVersionSelector", "preferredByCommander",
                       "lastCommanderId", "isUnsimulatedVersion",
                       "selectedVersionId", "versionById", "saveVersion"):
            self.assertIn(needle,script)
        self.assertIn("No cached simulations for",script)
        self.assertIn('class="deck-selection-row"',html)
        self.assertNotIn('id="deck-version-select"',html)
        self.assertIn(".deck-selection-row .global-deck-select",css)
        self.assertRegex(html, r'style\.css\?v=[^"]+')
        self.assertIn(".compact-selection",css)
        self.assertIn(".commander-picker",css)

    def test_independent_add_remove_controls_require_valid_full_deck_on_save(self):
        self.run_build()
        html=(self.destination/"editor.html").read_text(encoding="utf-8")
        js=(self.destination/"app.js").read_text(encoding="utf-8")
        self.assertIn('id="remove-one-button"',html)
        self.assertIn('id="add-one-button"',html)
        self.assertIn('id="save-local"',html)
        self.assertIn('function changeDraftQuantity(action)',js)
        self.assertIn('validateCounts(candidate,{allowIncomplete:true})',js)
        self.assertIn('validateCounts(activeCounts)',js)
        self.assertIn('$("save-local").disabled=total!==100',js)
        self.assertIn('$("export-deck").disabled=total!==100',js)
        self.assertIn('function hasUnsavedChanges()',js)

    def test_results_story_uses_derived_archive_insights_and_clickable_evidence(self):
        manifest=self.run_build()
        html=(self.destination/"index.html").read_text(encoding="utf-8")
        js=(self.destination/"app.js").read_text(encoding="utf-8")
        pure=(self.destination/"results_insights.js").read_text(encoding="utf-8")
        for key in ("results-kpis","results-takeaway","results-provenance",
                    "detail-opening","detail-resources","detail-candidates",
                    "story-summary-opening","story-meaning-resources",
                    "story-caveat-candidates","turn-timeline"):
            self.assertIn('id="'+key+'"',html)
        self.assertIn('./results_insights.js',html)
        self.assertIn("results_insights.js",manifest["asset_sha256"])
        self.assertIn("DeckInsights.summarize(archives[selected])",js)
        self.assertIn("DeckInsights.findings(aggregate)",js)
        self.assertIn('addEventListener("click",activate)',js)
        self.assertIn('bar.addEventListener("keydown"',js)
        self.assertIn("root.DeckInsights=api",pure)
        self.assertNotIn("results_sample_data",js)

    def test_all_canonical_commander_art_paths_are_optional_official_cdn(self):
        self.run_build()
        data=json.loads((self.destination/"decks.json").read_text())
        for deck in data["decks"]:
            image=data["cards"][deck["commander_id"]]["art"]
            self.assertIsNotNone(image)
            self.assertTrue(image.startswith("https://cards.scryfall.io/art_crop/front/"))
        self.assertIsNone(card_image({"id":"not-a-real-id"}))

    def test_optional_long_game_data_needs_exact_deck_revision(self):
        from tools.publish_game_outcomes import publish
        source=Path(self.temp.name)/"outcome-data"
        source.mkdir()
        key="mortarion_current"
        pinned=json.loads((Path(__file__).resolve().parents[1]/
            "web/pages/data/bounded-batches.json").read_text())
        sha=pinned["decks"][key]["deck_sha256"]
        counts={"win":0,"loss":0,"draw":0,"unresolved":1,"not_evaluated":0}
        life0={"round":0,"life_totals":dict(zip("0123",[40]*4)),
               "alive_seats":[0,1,2,3],"life_changes":[],"new_eliminations":[]}
        life1={"round":1,"life_totals":dict(zip("0123",[39,40,40,40])),
               "alive_seats":[0,1,2,3],"life_changes":[],"new_eliminations":[]}
        payload={
            "format":"commander-modeled-outcomes-v1","schema_version":1,
            "deck_key":key,"deck_sha256":sha,"scenario":"mixed",
            "requested_rounds":1,"seed_count":1,
            "pilot_style":"adaptive","provisional_mode":"safe",
            "opponent_fidelity":"abstract_opponent_pressure_not_card_exact",
            "outcomes_are_competitive_win_rates":False,
            "summary":{"total_games":1,"outcome_counts":counts},
            "runs":[{
                "seed":7,"completed_rounds":1,
                "outcome":{"status":"unresolved","complete":False,
                           "requested_rounds":1,"completed_rounds":1},
                "life_history":[life0,life1]
            }], "example_replays":[]
        }
        (source/"incoming.json").write_text(json.dumps(payload))
        staged=Path(self.temp.name)/"outcome-library"
        publish(source, staged, engine_commit="a"*40, deck_hashes={key:sha})
        output=self.run_build(outcome_source=staged)
        self.assertIn("game-outcomes/manifest.json",output["asset_sha256"])
        filename=f"{key}-mixed-adaptive-safe-r1.json"
        self.assertIn("game-outcomes/"+filename,output["asset_sha256"])
        self.assertEqual(
            json.loads((self.destination/"game-outcomes"/filename).read_text())
            ["outcomes_are_competitive_win_rates"],False)
        manifest=json.loads((self.destination/"game-outcomes/manifest.json").read_text())
        self.assertEqual(manifest["by_deck"],{key:[filename]})
        self.assertEqual(manifest["engine_commit"],"a"*40)
        payload["deck_sha256"]="wrong-hash"
        (staged/filename).write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError,"long-game export"):
            self.run_build(outcome_source=staged)

    def test_build_refuses_duplicate_seeds(self):
        with self.assertRaisesRegex(ValueError,"distinct"):
            self.run_build(seeds=(1,1))


if __name__=="__main__":
    unittest.main()
