"""Publish new simulation cohort while preserving only same-engine data.

This reuses the existing source-pinned game-outcomes publisher and validator.
"""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

from tools.publish_game_outcomes import (
    MAX_FILES, _filename, _hashes, publish, validate_batch, validate_library,
)


def append(source, output, *, engine_commit):
    source, output = Path(source), Path(output)
    batch = json.loads(source.read_text(encoding="utf-8"))
    hashes = _hashes()
    validate_batch(batch, deck_hashes=hashes)
    filename = _filename(batch)
    with tempfile.TemporaryDirectory(prefix="requested-game-release-") as temporary:
        staged = Path(temporary)
        if (output / "manifest.json").is_file():
            current = validate_library(output, deck_hashes=hashes)
            # Rule/pilot changes invalidate old cohorts. Pages/data-only
            # commits do not change the recorded engine source commit.
            if current["engine_commit"] == engine_commit:
                for item in current["files"]:
                    if item != filename:
                        shutil.copy2(output / item, staged / item)
        shutil.copy2(source, staged / filename)
        if len(list(staged.glob("*.json"))) > MAX_FILES:
            raise ValueError("Outcome library full; archive older cohorts")
        return publish(staged, output, engine_commit=engine_commit, deck_hashes=hashes)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engine-commit", required=True)
    args = parser.parse_args(argv)
    index = append(args.source, args.output, engine_commit=args.engine_commit)
    print(json.dumps({"engine_commit": index["engine_commit"],
                      "decks": len(index["by_deck"]),
                      "batches": len(index["files"])}, indent=2))


if __name__ == "__main__":
    main()
