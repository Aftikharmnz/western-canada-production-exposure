"""Commit an explicitly scoped, validated data release without overwriting newer work.

Scheduled AESO and ELT jobs can run independently. Rebase is allowed only when
remote changes do not touch this candidate's files or its parser/validation code.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CODE_PREFIXES = ("scripts/", ".github/workflows/", "src/")
CODE_FILES = {"data/sources.json", "data/asset_registry.csv", "data/refinery_capacity_overrides.json", "data/market_access_tariff_snapshot.json", "data/reference_source_monitors.json", "data/pipeline_route_facts.json"}


def git(*args, capture=True):
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, check=True,
                            stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else ""


def allowed_path(name: str) -> bool:
    path = PurePosixPath(name)
    return "\\" not in name and path.as_posix() == name and not path.is_absolute() and ".." not in path.parts and (
        name.startswith("public/data/") or name == "data/alerts/state.json")


def conflicting_changes(remote_paths: set[str], candidate_paths: set[str], protect_code=True) -> set[str]:
    return (remote_paths & candidate_paths) | ({name for name in remote_paths if
           name.startswith(CODE_PREFIXES) or name in CODE_FILES} if protect_code else set())


def publish(paths: list[str], base_sha: str, message: str, *, push=False, protect_code=True) -> bool:
    if not paths or any(not allowed_path(name) for name in paths):
        raise ValueError("Publication paths must be explicit generated data paths")
    if git("diff", "--cached", "--name-only"):
        raise ValueError("Index is not empty; refusing to include unrelated staged changes")
    git("add", "--", *paths)
    changed = set(git("diff", "--cached", "--name-only").splitlines())
    if not changed:
        print("No generated data changes to publish.")
        return False
    if not changed.issubset(set(paths)):
        raise ValueError("Unexpected files entered the publication commit")
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    git("commit", "-m", message, capture=False)
    if not push:
        return True
    for attempt in range(3):
        git("fetch", "origin", "main")
        remote_paths = set(git("diff", "--name-only", f"{base_sha}..origin/main").splitlines())
        conflicts = conflicting_changes(remote_paths, changed, protect_code)
        if conflicts:
            raise RuntimeError("A newer release or parser change overlaps this candidate; rerun from main. No force push performed. Files: " + ", ".join(sorted(conflicts)))
        git("rebase", "origin/main", capture=False)
        result = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, text=True, capture_output=True)
        if result.returncode == 0:
            print(result.stderr.strip())
            return True
        if attempt == 2 or not any(text in result.stderr.lower() for text in ("fetch first", "non-fast-forward", "failed to push some refs")):
            raise RuntimeError("GitHub rejected the generated data push; see repository permissions or concurrent updates")
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--paths", nargs="+")
    parser.add_argument("--base-sha")
    parser.add_argument("--message", default="Refresh verified official data")
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args()
    if bool(args.result) == bool(args.paths):
        parser.error("Provide either --result or --paths")
    result = json.loads(args.result.read_text(encoding="utf-8")) if args.result else {}
    paths = result.get("changed_paths", args.paths)
    base_sha = result.get("base_sha") or args.base_sha or git("rev-parse", "HEAD")
    # A failed ingestion can publish its failure status, never candidate data.
    if result.get("status") == "failed" and set(paths) != {"public/data/elt_status.json"}:
        raise ValueError("Failed candidate tried to publish data")
    published = publish(paths, base_sha, args.message, push=args.push)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as file:
            file.write(f"changed={'true' if published else 'false'}\n")


if __name__ == "__main__":
    main()
