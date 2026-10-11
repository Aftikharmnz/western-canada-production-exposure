"""Stage, validate and describe a website-data release. Never pushes to GitHub.

Official source parsers own extraction and normalization. This coordinator owns
the release boundary: a failed candidate never replaces published observations.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INFRASTRUCTURE_MONITOR_FILES = {"elt_status.json", "reference_source_status.json", "api_health.json", "eia_refinery_capacity.json"}
INFRASTRUCTURE_GEOJSON_FILES = {"aer_feeder_pipelines.geojson", "aer_pipeline_installations.geojson",
                              "market_access_pipelines.geojson", "railways.geojson"}
GEOJSON_REFRESH_METADATA = {"generated_at", "source_retrieved_at", "source_last_modified", "source_sha256"}
AER_REFRESH_RECEIPT_FIELDS = {"checked_at", "retrieved_at", "source_last_modified", "sha256", "bytes", "etag",
                              "content_changed", "download_content_changed", "fetch_status"}


def read_json(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_json(path: Path, value: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def file_changes(baseline: Path, candidate: Path) -> list[str]:
    names = {path.relative_to(root).as_posix() for root in (baseline, candidate) for path in root.rglob("*") if path.is_file()}
    return sorted(name for name in names if not (baseline / name).is_file() or not (candidate / name).is_file()
                  or digest(baseline / name) != digest(candidate / name))


def infrastructure_header(value: dict, *, index=False) -> dict:
    """Exclude refresh receipts only; feature properties and substantive metadata remain intact."""
    result = dict(value)
    if index:
        result.pop("generated_at", None)
        result["sources"] = {name: {key: item for key, item in receipt.items() if key not in AER_REFRESH_RECEIPT_FIELDS}
                             for name, receipt in value.get("sources", {}).items()}
    elif isinstance(value.get("metadata"), dict):
        result["metadata"] = {key: item for key, item in value["metadata"].items() if key not in GEOJSON_REFRESH_METADATA}
    return result


def geojson_header_end(text: str) -> tuple[dict, int] | None:
    """Read top-level members up to features without decoding the large geometry array."""
    decoder, header, position = json.JSONDecoder(), {}, 0
    def whitespace(index):
        while index < len(text) and text[index].isspace():
            index += 1
        return index
    position = whitespace(position)
    if position >= len(text):
        return None
    if text[position] != "{":
        raise ValueError("Expected a GeoJSON object")
    position += 1
    try:
        while True:
            position = whitespace(position)
            key, position = decoder.raw_decode(text, position)
            position = whitespace(position)
            if position >= len(text):
                return None
            if text[position] != ":":
                raise ValueError("Malformed GeoJSON member")
            position = whitespace(position + 1)
            if position >= len(text):
                return None
            if key == "features":
                if text[position] != "[":
                    raise ValueError("Expected a GeoJSON feature array")
                return header, position
            header[key], position = decoder.raw_decode(text, position)
            position = whitespace(position)
            if position >= len(text):
                return None
            if text[position] != ",":
                raise ValueError("GeoJSON features must follow its header")
            position += 1
    except json.JSONDecodeError:
        return None


def infrastructure_geojson_digest(path: Path) -> str:
    """Hash the generated feature body verbatim and normalize only its small metadata header."""
    with path.open(encoding="utf-8") as source:
        prefix = ""
        while len(prefix) < 2 * 1024 * 1024:
            chunk = source.read(64 * 1024)
            if not chunk:
                break
            prefix += chunk
            parsed = geojson_header_end(prefix)
            if parsed is not None:
                header, position = parsed
                hasher = hashlib.sha256(json.dumps(infrastructure_header(header), sort_keys=True, separators=(",", ":")).encode())
                hasher.update(b"\0")
                hasher.update(prefix[position:].encode())
                for chunk in iter(lambda: source.read(1024 * 1024), ""):
                    hasher.update(chunk.encode())
                return hasher.hexdigest()
    # An unfamiliar layout stays conservatively changed, never silently ignored.
    return digest(path)


def infrastructure_data_changed(baseline: Path, candidate: Path, changes: list[str]) -> bool:
    meaningful = set(changes) - INFRASTRUCTURE_MONITOR_FILES
    # Category/tile additions, removals, and edits already prove a real change.
    if meaningful - INFRASTRUCTURE_GEOJSON_FILES - {"aer_pipeline_index.json"}:
        return True
    for name in sorted(meaningful):
        before, after = baseline / name, candidate / name
        if not before.is_file() or not after.is_file():
            return True
        if name == "aer_pipeline_index.json":
            if infrastructure_header(read_json(before), index=True) != infrastructure_header(read_json(after), index=True):
                return True
        elif infrastructure_geojson_digest(before) != infrastructure_geojson_digest(after):
            return True
    return False


def run_script(script: str, arguments: list[str], log_dir: Path, timeout=1800):
    print(f"Running {script}", flush=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / (Path(script).stem + ".log")).open("w", encoding="utf-8") as output:
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *arguments], cwd=ROOT,
                                stdout=output, stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"{script} did not complete successfully; see its run log")


def workflow_url() -> str | None:
    repository, run_id = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_RUN_ID", "")
    if repository and run_id.isdigit():
        return f"https://github.com/{repository}/actions/runs/{run_id}"
    return None


def release_status(previous: dict, *, mode: str, timestamp: str, data_changed: bool,
                   failed: bool, warnings: list[str], run_url: str | None, manifest: dict) -> dict:
    value = dict(previous or {})
    value["schema_version"] = 1
    value["policy"] = {"production": "Official reported actuals only", "production_checks": "Daily",
                       "revision_window_months": 3, "infrastructure_checks": "Weekly",
                       "power_checks": "Every 30 minutes", "publication": "Validated releases only"}
    prior = value.get(mode, {})
    value[mode] = {"checked_at": timestamp,
                   "raw_archive_url": prior.get("raw_archive_url"),
                   "last_data_update": timestamp if data_changed and not failed else prior.get("last_data_update"),
                   "status": "failed" if failed else "degraded" if warnings else "updated" if data_changed else "unchanged",
                   "run_url": run_url, "warnings": warnings,
                   "latest_actual_date": manifest.get("latest_actual_date"),
                   "default_date": manifest.get("default_date")}
    return value


def promote_files(baseline: Path, candidate: Path, changes: list[str]):
    """Local checkout promotion; Git commit and Pages deployment are the atomic public boundary."""
    for name in changes:
        source, destination = (candidate / name).resolve(), (baseline / name).resolve()
        if not source.is_relative_to(candidate.resolve()) or not destination.is_relative_to(baseline.resolve()):
            raise ValueError("Candidate path escaped its data directory")
        if source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name + ".elt-tmp")
            shutil.copyfile(source, temporary)
            temporary.replace(destination)
        elif destination.is_file():
            destination.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["production", "infrastructure"], default="production")
    parser.add_argument("--baseline-dir", type=Path, default=ROOT / "public/data")
    parser.add_argument("--work-dir", type=Path, default=ROOT / "data/processed/elt-run")
    parser.add_argument("--sources", default=None)
    parser.add_argument("--update-months", type=int, default=3)
    parser.add_argument("--history-start", default=None)
    parser.add_argument("--full-revision-scan", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--skip-references", action="store_true")
    parser.add_argument("--promote", action="store_true", help="Copy validated changes into the checkout; never commit or push")
    args = parser.parse_args()
    if args.mode == "infrastructure" and args.offline:
        parser.error("Use build_aer_infrastructure.py --offline for a scoped AER replay; the full infrastructure check requires online services")
    if not 1 <= args.update_months <= 120:
        parser.error("--update-months must be 1 through 120")
    baseline, work = args.baseline_dir.resolve(), args.work_dir.resolve()
    if work == baseline or work.is_relative_to(baseline) or baseline.is_relative_to(work):
        parser.error("Work and published data directories must be separate")
    candidate = work / "candidate"
    work.mkdir(parents=True, exist_ok=True)
    if candidate.exists():
        parser.error("Candidate directory already exists; use a new work directory")
    shutil.copytree(baseline, candidate)
    timestamp, warnings, errors = now(), [], []
    base_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    ingestion = {}
    infrastructure_checks = []
    if args.mode == "production":
        arguments = ["--baseline-dir", str(baseline), "--output-dir", str(candidate),
                     "--update-months", str(args.update_months), "--result-json", str(work / "ingestion.json")]
        arguments.append("--offline" if args.offline else "--download")
        if args.sources:
            arguments.extend(["--sources", args.sources])
        if args.history_start:
            arguments.extend(["--history-start", args.history_start])
        if args.full_revision_scan:
            arguments.append("--full-revision-scan")
        try:
            run_script("run_etl.py", arguments, work / "logs", timeout=4 * 3600)
            ingestion = read_json(work / "ingestion.json", {})
            if ingestion.get("status") == "failed":
                raise RuntimeError("Production ingestion reported failure")
            if ingestion.get("errors"):
                warnings.append("Some official sources could not refresh; their previously validated observations are retained.")
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            ingestion = read_json(work / "ingestion.json", {})
            errors.extend(ingestion.get("errors") or [str(error)])
    else:
        try:
            run_script("build_aer_infrastructure.py", ["--data-dir", str(candidate), "--baseline-dir", str(baseline),
                       "--report", str(work / "aer_infrastructure_result.json")], work / "logs", timeout=1800)
            infrastructure_checks = read_json(work / "aer_infrastructure_result.json", {}).get("checks", [])
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            # This family contains an index, categories and many tiles. Reject
            # the whole candidate if installation fails at any point.
            errors.append(str(error))
        for script, name in [("build_market_access_pipelines.py", "market_access_pipelines.geojson"),
                             ("build_railway_layer.py", "railways.geojson")]:
            try:
                arguments = ["--output", str(candidate / name)]
                if script == "build_market_access_pipelines.py":
                    arguments.extend(["--aer-feeder-input", str(candidate / "aer_feeder_pipelines.geojson")])
                run_script(script, arguments, work / "logs", timeout=600)
            except (RuntimeError, subprocess.TimeoutExpired):
                shutil.copyfile(baseline / name, candidate / name)
                warnings.append(f"{name}: upstream refresh unavailable; validated existing layer retained.")
        try:
            run_script("audit_live_apis.py", ["--output", str(candidate / "api_health.json")], work / "logs", timeout=240)
        except (RuntimeError, subprocess.TimeoutExpired):
            warnings.append("Some live weather, wildfire or map services are unavailable; see API health details.")
    reference = {}
    if not args.skip_references and not args.offline:
        try:
            run_script("check_reference_sources.py", ["--output", str(candidate / "reference_source_status.json"),
                       "--eia-output", str(candidate / "eia_refinery_capacity.json"),
                       "--baseline", str(baseline / "reference_source_status.json"),
                       "--eia-baseline", str(baseline / "eia_refinery_capacity.json")], work / "logs", timeout=900)
            reference = read_json(candidate / "reference_source_status.json", {})
            if reference.get("review_required_count"):
                warnings.append(f"{reference['review_required_count']} reference sources need review; reviewed facts retain their original verification dates.")
        except (RuntimeError, subprocess.TimeoutExpired):
            for name in ("reference_source_status.json", "eia_refinery_capacity.json"):
                if (baseline / name).is_file():
                    shutil.copyfile(baseline / name, candidate / name)
                elif (candidate / name).exists():
                    (candidate / name).unlink()
            warnings.append("Reference-source monitoring did not complete; previous reviewed values retained.")
    if not errors:
        try:
            run_script("validate_production_data.py", ["--data-dir", str(candidate)], work / "logs", timeout=600)
            run_script("validate_infrastructure_layers.py", ["--data-dir", str(candidate)], work / "logs", timeout=600)
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            errors.append(str(error))
    changes = [] if errors else file_changes(baseline, candidate)
    observed_data_changed = (bool(ingestion.get("candidate_changed")) if args.mode == "production"
                             else infrastructure_data_changed(baseline, candidate, changes))
    previous_status = read_json(baseline / "elt_status.json", {})
    status = release_status(previous_status, mode=args.mode, timestamp=timestamp,
                            data_changed=observed_data_changed, failed=bool(errors), warnings=warnings,
                            run_url=workflow_url(), manifest=read_json((baseline if errors else candidate) / "manifest.json", {}))
    status[args.mode]["execution_mode"] = "offline_replay" if args.offline else "online"
    status[args.mode]["last_attempt_at"] = timestamp
    if args.offline:
        status[args.mode]["checked_at"] = previous_status.get(args.mode, {}).get("checked_at")
    if errors:
        status[args.mode]["warnings"] = ["The refresh did not pass validation. The last published dataset is retained."]
    write_json(candidate / "elt_status.json", status)
    changes = ["elt_status.json"] if errors else file_changes(baseline, candidate)
    receipts = list(ingestion.get("checks", [])) + infrastructure_checks
    for check in reference.get("checks", []):
        if check.get("raw_path") and check.get("sha256") and check.get("facts_automatically_updated"):
            receipt = dict(check)
            receipt["source_id"] = check.get("id")
            receipt["raw_path"] = check["raw_path"].removeprefix("data/raw/")
            receipt["url"] = check.get("source_url", check.get("url"))
            receipts.append(receipt)
    result = {"schema_version": 1, "mode": args.mode, "started_at": timestamp, "finished_at": now(),
              "base_sha": base_sha, "parser_revision": base_sha, "candidate_dir": str(candidate), "baseline_dir": str(baseline),
              "status": "failed" if errors else "degraded" if warnings else "success",
              "data_changed": observed_data_changed and not bool(errors),
              "changed_paths": ["public/data/" + name for name in changes],
              "warnings": warnings, "errors": errors, "checks": receipts,
              "run_url": workflow_url()}
    summary = [f"# {args.mode.title()} data refresh", "", f"Result: **{result['status']}**", "",
               f"Changed public files: {len(changes)}. Data changed: {result['data_changed']}.", "",
               "Only validated candidates replace published observations."]
    summary += ["", *[f"- {item}" for item in warnings + errors]] if warnings or errors else []
    (work / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    if args.promote:
        promote_files(baseline, candidate, changes)
    # This file authorizes publication. Do not create it until every local
    # replacement succeeded; a partially promoted checkout must never publish.
    write_json(work / "pipeline_result.json", result)
    print(json.dumps({key: result[key] for key in ("status", "data_changed", "changed_paths")}), flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
