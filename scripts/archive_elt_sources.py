"""Package exact official input bytes for durable GitHub Release attachments.

The source cache is an accelerator, not an archive. Packages contain only the
registered raw files whose checksums match successful ingestion receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def reviewed_inputs(result: dict, raw_dir: Path = RAW) -> list[tuple[Path, dict]]:
    if result.get("status") == "failed":
        return []
    verified = {}
    for check in result.get("checks", []):
        name, expected = check.get("raw_path"), check.get("sha256")
        if not name or not expected or check.get("status") in {"failed", "not_published"}:
            continue
        if not check.get("content_changed", False):
            continue
        source = (raw_dir / name).resolve()
        if not source.is_relative_to(raw_dir.resolve()) or source.is_symlink():
            raise ValueError("Raw-source receipt escaped the allowed source directory")
        if not source.is_file() or sha256(source) != expected:
            raise ValueError(f"Raw source does not match its ingestion receipt: {name}")
        # Never include arbitrary workbook paths or whole cache directories.
        if not str(check.get("url", "")).startswith(("https://", "http://")):
            raise ValueError(f"Official source URL missing: {name}")
        verified[name] = (source, {key: check.get(key) for key in
                                  ("source_id", "url", "raw_path", "sha256", "bytes", "checked_at", "period", "publication_period")})
    return [verified[name] for name in sorted(verified)]


def package_sources(result: dict, output: Path, raw_dir: Path = RAW, max_part_bytes=450 * 1024 * 1024) -> dict:
    inputs = reviewed_inputs(result, raw_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": 1, "run_url": result.get("run_url"), "base_sha": result.get("base_sha"), "parser_revision": result.get("parser_revision", result.get("base_sha")),
                "created_at": result.get("finished_at"), "source_files": [], "archives": []}
    batches, batch, batch_size = [], [], 0
    for source, receipt in inputs:
        if source.stat().st_size >= 1900 * 1024 * 1024:
            raise ValueError("Source is too large for a GitHub Release asset")
        if batch and batch_size + source.stat().st_size > max_part_bytes:
            batches.append(batch)
            batch, batch_size = [], 0
        batch.append((source, receipt))
        batch_size += source.stat().st_size
    if batch:
        batches.append(batch)
    for number, entries in enumerate(batches, 1):
        archive = output / f"official-inputs-{number:03d}.zip"
        if archive.exists():
            raise ValueError("Archive already exists; immutable source packages must not be overwritten")
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as bundle:
            for source, receipt in entries:
                bundle.write(source, receipt["raw_path"])
                manifest["source_files"].append({**receipt, "archive": archive.name})
        manifest["archives"].append({"name": archive.name, "bytes": archive.stat().st_size, "sha256": sha256(archive)})
    (output / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--publish", action="store_true", help="Upload exact inputs to a new GitHub Release before publishing data")
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    manifest = package_sources(result, args.output_dir)
    if args.publish and manifest["archives"]:
        repository = os.environ.get("GITHUB_REPOSITORY", "")
        run_id, attempt = os.environ.get("GITHUB_RUN_ID", ""), os.environ.get("GITHUB_RUN_ATTEMPT", "1")
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository) or not run_id.isdigit() or not attempt.isdigit():
            raise ValueError("GitHub run identity is required for immutable raw-source publication")
        tag = f"elt-raw-{run_id}-{attempt}"
        notes = args.output_dir / "release-notes.md"
        notes.write_text(f"Exact official source inputs for [data refresh]({result.get('run_url')}). "
                         "SHA-256 receipts are in source-manifest.json. Replay uses the baseline commit recorded there plus these changed inputs.\n", encoding="utf-8")
        assets = [str(args.output_dir / item["name"]) for item in manifest["archives"]]
        assets.append(str(args.output_dir / "source-manifest.json"))
        subprocess.run(["gh", "release", "create", tag, *assets, "--repo", repository,
                        "--target", result["base_sha"], "--latest=false", "--title", f"Official source archive {run_id}.{attempt}",
                        "--notes-file", str(notes)], check=True)
        url = f"https://github.com/{repository}/releases/tag/{tag}"
        result["raw_archive_url"] = url
        for directory in {result["candidate_dir"], result["baseline_dir"]}:
            status_path = Path(directory) / "elt_status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status[result["mode"]]["raw_archive_url"] = url
            status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8", newline="\n")
        args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"source_count": len(manifest["source_files"]), "archive_count": len(manifest["archives"])}))


if __name__ == "__main__":
    main()
