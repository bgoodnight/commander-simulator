"""Deterministic source-tree storage audit; uses git metadata, not checkout sizes.

The sum of tracked file sizes is NOT GitHub's repository billing/storage usage:
Git deduplicates equal blobs and compresses its object database. This is a
working-tree/publication growth diagnostic, not a substitute for R2 inventory.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import subprocess

MIB = 1024 * 1024
MIRRORS = (
    ("docs/deck-lab/simulation-data/", "web/pages/data/simulation-archive/"),
    ("docs/deck-lab/gorge-data/", "web/pages/data/gorge/"),
    ("docs/deck-lab/game-outcomes/", "web/pages/data/game-outcomes/"),
)


def tracked_entries():
    raw = subprocess.check_output(["git", "ls-tree", "-r", "-l", "-z", "HEAD"])
    entries = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, kind, sha, size = metadata.split()
        if kind != b"blob" or size == b"-":
            continue
        entries.append((path.decode("utf-8"), sha.decode("ascii"), int(size)))
    return entries


def inventory(entries):
    by_path = {path: (sha, size) for path, sha, size in entries}
    folders = defaultdict(lambda: {"files": 0, "bytes": 0})
    hashes = defaultdict(list)
    for path, sha, size in entries:
        category = path.split("/", 1)[0]
        folders[category]["files"] += 1
        folders[category]["bytes"] += size
        hashes[sha].append((path, size))

    repeated_bytes = sum(
        (len(paths) - 1) * paths[0][1]
        for paths in hashes.values() if len(paths) > 1
    )
    mirrors = []
    for left, right in MIRRORS:
        pairs = [
            (path, right + path[len(left):], size)
            for path, sha, size in entries
            if path.startswith(left) and
            right + path[len(left):] in by_path and
            by_path[right + path[len(left):]][0] == sha
        ]
        mirrors.append({
            "source": left, "mirror": right,
            "identical_pairs": len(pairs),
            "repeated_bytes": sum(p[2] for p in pairs),
        })

    releases = set()
    for path, _, _ in entries:
        prefix = "web/pages/data/simulation-archive/releases/"
        if path.startswith(prefix):
            releases.add(path[len(prefix):].split("/", 1)[0])

    return {
        "schema": "commander-storage-audit-v1",
        "file_count": len(entries),
        "tracked_content_bytes": sum(size for _, _, size in entries),
        "unique_blob_content_bytes": sum(paths[0][1] for paths in hashes.values()),
        "duplicate_worktree_bytes": repeated_bytes,
        "historical_simulation_releases": len(releases),
        "by_top_level": dict(sorted(folders.items())),
        "known_mirrors": mirrors,
        "largest_files": [
            {"path": path, "bytes": size}
            for path, _, size in sorted(entries, key=lambda row: row[2], reverse=True)[:12]
        ],
    }


def markdown(report):
    mb = lambda n: f"{n / MIB:.1f}"
    lines = [
        "## Commander Simulator storage inventory",
        "",
        f"- Tracked files: {report['file_count']:,}",
        f"- Sum of checked-out file contents: {mb(report['tracked_content_bytes'])} MiB",
        f"- Identical-content duplication in checkout: {mb(report['duplicate_worktree_bytes'])} MiB",
        f"- Distinct Git blob payloads before compression: {mb(report['unique_blob_content_bytes'])} MiB",
        f"- Legacy simulation release identifiers: {report['historical_simulation_releases']}",
        "",
        "These are uncompressed file sizes, **not** the GitHub repository's on-disk/billed size.",
        "Git stores identical blobs once; neither Git history nor Actions artifacts nor R2 are counted here.",
        "",
        "| Source directory | Tracked files | MiB |",
        "|---|---:|---:|",
    ]
    for name, data in sorted(report["by_top_level"].items(),
                             key=lambda item: item[1]["bytes"], reverse=True):
        lines.append(f"| {name} | {data['files']:,} | {mb(data['bytes'])} |")
    lines.extend(["", "### Known generated/publication mirrors", "",
                  "| Source | Mirror | Matching files | Repeated MiB |",
                  "|---|---|---:|---:|"])
    for m in report["known_mirrors"]:
        lines.append(
            f"| {m['source']} | {m['mirror']} | {m['identical_pairs']} | "
            f"{mb(m['repeated_bytes'])} |"
        )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--github-summary", action="store_true")
    args = parser.parse_args()
    report = inventory(tracked_entries())
    summary = markdown(report)
    print(summary)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n")
    if args.github_summary and os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as out:
            out.write(summary)


if __name__ == "__main__":
    main()
