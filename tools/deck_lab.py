"""Serve the M1/U1 local Commander Deck Lab with versioned offline drafts.

Start from repo root: python tools/deck_lab.py
Open http://127.0.0.1:8765/. The local server never calls Scryfall, executes
unimplemented card rules, or modifies a deck or catalog. Stop with Ctrl+C.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from commander_sim.deck_lab_api import (
    catalog_response, deck_detail, observation_response
)
from commander_sim.card_discovery import local_suggestions
from commander_sim.deck_fixtures import SHARED_CATALOG
from commander_sim.deck_workspace import compose_draft, save_draft, saved_versions

HTML_PATH = ROOT / "web" / "deck_lab.html"


def respond(path, parameters, *, catalog_path=None, output_dir=None):
    """Pure read-only router for testing without binding a server socket."""
    def only(name, default=None):
        values = parameters.get(name, [])
        if not values:
            return default
        if len(values) != 1:
            raise ValueError("Exactly one " + name + " parameter is required")
        return values[0]

    options = {}
    if catalog_path is not None:
        options["catalog_path"] = catalog_path
    if output_dir is not None:
        options["output_dir"] = output_dir

    if path == "/api/cards/suggest":
        query = only("q", "")
        if len(query) > 150:
            raise ValueError("Suggestion query too long")
        # This endpoint deliberately performs zero network calls. Online name
        # completion is an opt-in UI feature for a later milestone.
        return {"query": query, "source": "local_cache",
                "suggestions": local_suggestions(
                    query, catalog_path=options.get("catalog_path", SHARED_CATALOG)
                )}
    if path == "/api/versions":
        return {"versions": saved_versions()}
    if path == "/api/decks":
        return catalog_response(**options)
    if path == "/api/deck":
        key = only("key")
        if not key:
            raise ValueError("Missing deck key")
        return deck_detail(key, **options)
    if path == "/api/observation":
        key = only("key")
        if not key:
            raise ValueError("Missing deck key")
        try:
            seed = int(only("seed", "0"))
            turns = int(only("turns", "6"))
        except ValueError as exc:
            raise ValueError("Seed and turns must be integers") from exc
        return observation_response(key, seed=seed, turns=turns, **options)
    raise KeyError("Unknown local API route")


def post_response(path, payload, *, catalog_path=None, workspace=None):
    """Strict local-only U1 routes: preview and Save As, no network."""
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object")
    if set(payload) != {"base_key", "changes"} and set(payload) != {"base_key", "changes", "title"}:
        raise ValueError("Unexpected draft fields")
    options = {}
    if catalog_path is not None:
        options["catalog_path"] = catalog_path
    if path == "/api/draft/preview":
        if "title" in payload:
            raise ValueError("Title is only accepted when saving")
        draft = compose_draft(payload["base_key"], payload["changes"], **options)
        # The full text is only needed for a save, not in the UI response.
        return {key: value for key, value in draft.items() if key != "deck_text"}
    if path == "/api/draft/save":
        if "title" not in payload:
            raise ValueError("Missing title")
        if workspace is not None:
            options["workspace"] = workspace
        return save_draft(payload["base_key"], payload["changes"], payload["title"], **options)
    raise KeyError("Unknown local draft route")


class Handler(BaseHTTPRequestHandler):
    def send_payload(self, status, content_type, raw):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        # Local browser only. Cross-origin websites cannot silently write
        # decks through localhost; require the correct origin and JSON.
        origin = self.headers.get("Origin")
        host = self.headers.get("Host", "")
        scheme_origin = "http://" + host
        if (origin != scheme_origin or
            not (host.startswith("127.0.0.1:") or host.startswith("localhost:"))):
            self.send_payload(403, "application/json; charset=utf-8",
                              b'{"error":"Local Deck Lab origin required"}')
            return
        try:
            if self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/json":
                raise ValueError("Content-Type must be application/json")
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 32000:
                raise ValueError("Draft request size must be at most 32 KB")
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
            result = post_response(urlparse(self.path).path, payload)
            status = 200
        except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
            status = 404 if isinstance(exc, KeyError) else 400
            result = {"error": str(exc)}
        self.send_payload(status, "application/json; charset=utf-8",
                          json.dumps(result, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        request = urlparse(self.path)
        if request.path in ("/", "/index.html"):
            self.send_payload(200, "text/html; charset=utf-8",
                              HTML_PATH.read_bytes())
            return
        try:
            payload = respond(request.path, parse_qs(request.query))
            code = 200
        except (ValueError, KeyError, OSError, TypeError) as exc:
            payload = {"error": str(exc)}
            code = 404 if isinstance(exc, KeyError) else 400
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_payload(code, "application/json; charset=utf-8", raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1",
                        help="Bind address (default local-only 127.0.0.1)")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")
    with ThreadingHTTPServer((args.host, args.port), Handler) as server:
        print(f"Commander Deck Lab: http://{args.host}:{args.port}/", flush=True)
        print("Offline observation and editable Save As variants; no card effects or API fetching.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
