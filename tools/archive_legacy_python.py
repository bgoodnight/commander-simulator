"""Build a complete, immutable, checksum-verified backup of legacy Python runs.

This tool is read-only against source files. It has no R2 credentials and never
modifies the current Gorge warehouses, native traces or public replay catalog.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

from tools.publish_simulation_archive import validate_index

SCHEMA = "commander-legacy-python-r2-archive-v1"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_paths(source: Path):
    """Validate every referenced source file; reject unindexed or symlink data."""
    index = validate_index(source)
    names = {"manifest.json"}
    for release in index["releases"]:
        for entry in release["decks"].values():
            names.add(entry["manifest"])
            names.add(entry["runs"])
    actual = set()
    for path in source.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlinks cannot be archived: {path}")
        if path.is_file():
            actual.add(path.relative_to(source).as_posix())
    if names != actual:
        raise ValueError(
            f"Archive inventory mismatch: missing={sorted(names-actual)[:5]}, "
            f"unexpected={sorted(actual-names)[:5]}"
        )
    for relative in names:
        parts = PurePosixPath(relative)
        if parts.is_absolute() or ".." in parts.parts:
            raise ValueError(f"Unsafe relative path: {relative}")
    return index, sorted(names)


def make_bundle(source: Path, output: Path):
    """Create reproducible tar.gz and independent SHA/byte-count metadata."""
    source, output = Path(source), Path(output)
    index, files = source_paths(source)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / "legacy-python-source.tar.gz"
    manifest_bytes = (source / "manifest.json").read_bytes()
    entries = []
    # Metadata normalization prevents tar/gzip timestamps from changing
    # the backup hash when the source tree is unchanged.
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w") as tar:
                for relative in files:
                    content = (source / relative).read_bytes()
                    info = tarfile.TarInfo(name=relative)
                    info.size = len(content)
                    info.mtime = 0
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    info.mode = 0o644
                    tar.addfile(info, io.BytesIO(content))
                    entries.append({
                        "path": relative, "sha256": sha256(content),
                        "bytes": len(content)
                    })
    digest = sha256(archive.read_bytes())
    manifest_digest = sha256(manifest_bytes)
    key = f"legacy-python/v1/{manifest_digest[:16]}/{digest}.tar.gz"
    metadata = {
        "schema": SCHEMA,
        "r2_bucket": "gorge-simulations",
        "r2_object_key": key,
        "r2_archive_sha256": digest,
        "r2_archive_bytes": archive.stat().st_size,
        "source_manifest_sha256": manifest_digest,
        "release_count": len(index["releases"]),
        "source_file_count": len(files),
        "source_total_bytes": sum(row["bytes"] for row in entries),
        "files": entries,
    }
    (output / "inventory.json").write_text(
        json.dumps(metadata, sort_keys=True, separators=(",", ":")) + "\n"
    )
    return metadata


def verify_download(archive: Path, metadata: dict):
    """Verify downloaded bytes AND every member against the source inventory."""
    if sha256(archive.read_bytes()) != metadata["r2_archive_sha256"]:
        raise ValueError("R2 roundtrip archive SHA-256 mismatch")
    expected = {f["path"]: f for f in metadata["files"]}
    found = set()
    with tarfile.open(archive, mode="r:gz") as tar:
        for member in tar:
            if not member.isfile() or member.name not in expected or member.name in found:
                raise ValueError(f"Unexpected or duplicate R2 archive member: {member.name}")
            data = tar.extractfile(member).read()
            row = expected[member.name]
            if len(data) != row["bytes"] or sha256(data) != row["sha256"]:
                raise ValueError(f"Archived member checksum mismatch: {member.name}")
            found.add(member.name)
    if found != expected.keys():
        raise ValueError("Incomplete R2 backup contents")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=Path("web/pages/data/simulation-archive"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--verify-download", type=Path)
    parser.add_argument("--inventory", type=Path)
    args = parser.parse_args()
    if args.verify_download:
        if not args.inventory:
            parser.error("--verify-download requires --inventory")
        meta = json.loads(args.inventory.read_text())
        verify_download(args.verify_download, meta)
        print("LEGACY_PYTHON_R2_DOWNLOAD_VERIFIED", meta["r2_archive_sha256"])
    else:
        if not args.out:
            parser.error("--out required when creating an archive")
        result = make_bundle(args.source, args.out)
        # Small, stable output appropriate for verification logs (no file keys).
        print("LEGACY_PYTHON_R2_ARCHIVE", json.dumps({
            key: result[key] for key in (
                "r2_object_key", "r2_archive_sha256", "r2_archive_bytes",
                "source_manifest_sha256", "release_count", "source_file_count",
                "source_total_bytes"
            )
        }, sort_keys=True))


if __name__ == "__main__":
    main()
