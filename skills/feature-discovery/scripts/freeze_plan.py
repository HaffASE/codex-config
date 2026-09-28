#!/usr/bin/env python3
"""Copy a validated draft into a new, hash-bound review revision. No verdicts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from common import InvalidPlan, REVISION, digest, file_bytes, load_json, need, safe_path, text, verify_snapshot
from validate_plan import validate_content


def architectural_decisions(plan: dict[str, Any]) -> dict[str, Any]:
    # Conservative: even an editorial edit to a shared/security decision triggers a full review.
    return {d["id"]: d for d in plan["decisions"] if d["category"] in {"architecture", "security"}}


def freeze(run: Path, revision: str, mode: str = "full", impact: list[str] | None = None,
           reason: str = "Complete review of the current packet.") -> dict[str, Any]:
    need(bool(REVISION.fullmatch(revision)), "Use revision names r01, r02, ...")
    need(mode in {"full", "delta"}, "Review mode must be full or delta")
    text(reason, "Review scope rationale")
    # Validate both source and captured bytes. The final copy is rechecked before publishing.
    draft = run / "draft"
    plan = validate_content(draft)
    captured = file_bytes(draft)
    revisions = safe_path(run, "revisions")
    revisions.mkdir(exist_ok=True)
    # Single-coordinator concurrency guard. A crash can leave the lock; never auto-remove it.
    lock = safe_path(run, ".freeze.lock")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    tmp: Path | None = None
    try:
        os.close(fd)
        existing = sorted(p.name for p in revisions.iterdir() if p.is_dir() and REVISION.fullmatch(p.name))
        existing.sort(key=lambda x: int(x[1:]))
        expected = len(existing) + 1
        need([int(x[1:]) for x in existing] == list(range(1, expected)), "Revision sequence has gaps or duplicate numeric revisions")
        need(int(revision[1:]) == expected and revision == f"r{expected:02d}", f"Next revision must be r{expected:02d}")
        need(expected <= plan["review_policy"]["max_rounds"], "Review budget exhausted; stop with unresolved findings")
        destination = safe_path(run, f"revisions/{revision}")
        need(not destination.exists(), "A frozen revision cannot be overwritten")
        current_hashes = {name: hashlib.sha256(data).hexdigest() for name, data in captured.items()}
        base = existing[-1] if existing else None
        base_digest: str | None = None
        changed = set(current_hashes)
        deleted: set[str] = set()
        if base:
            old_manifest, old_root = verify_snapshot(run, base)
            old_plan = validate_content(old_root)
            base_digest = old_manifest["packet_digest"]
            need(plan["review_policy"] == old_plan["review_policy"], "Do not change review policy or reset budgets mid-run")
            need(plan["task_id"] == old_plan["task_id"] and plan["profile"] == old_plan["profile"], "Task/profile cannot change mid-run")
            changed = {name for name, sha in current_hashes.items() if old_manifest["files"].get(name) != sha}
            deleted = set(old_manifest["files"]) - set(current_hashes)
            if architectural_decisions(plan) != architectural_decisions(old_plan):
                need(mode == "full", "Shared architecture/security decisions changed: full review required")
            for role in plan["review_policy"]["roles"]:
                # A delta cannot be based on an unreviewed packet. Full reruns also preserve the findings ledger.
                from validate_plan import review_for
                review_for(run, base, role)
        else:
            need(mode == "full", "First review must be full")
        impact_set = set(impact or [])
        need(impact_set <= set(current_hashes), f"Unknown impacted files: {sorted(impact_set - set(current_hashes))}")
        if mode == "delta":
            need(bool(impact_set), "Delta review requires an explicit impact set, even when it equals changed files")
        required = set(current_hashes) if mode == "full" else changed | impact_set
        manifest: dict[str, Any] = {
            "schema_version": 1, "revision": revision, "base_revision": base,
            "base_digest": base_digest, "review_mode": mode,
            "required_review_files": sorted(required), "impact_rationale": reason,
            "changed_files": sorted(changed), "deleted_files": sorted(deleted), "files": current_hashes,
        }
        manifest["packet_digest"] = digest(manifest)
        tmp = Path(tempfile.mkdtemp(prefix=".capture-", dir=revisions))
        packet = tmp / "packet"
        packet.mkdir()
        for name, data in captured.items():
            target = safe_path(packet, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        captured_plan = validate_content(packet)
        need(captured_plan == plan, "Draft changed while being captured; retry with a stable draft")
        (tmp / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.rename(destination)
        tmp = None
        return manifest
    finally:
        if tmp is not None:
            shutil.rmtree(tmp)
        lock.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--mode", choices=["full", "delta"], default="full")
    parser.add_argument("--impact", action="append", default=[])
    parser.add_argument("--reason", default="Complete review of the current packet.")
    args = parser.parse_args()
    try:
        manifest = freeze(args.run, args.revision, args.mode, args.impact, args.reason)
        print(json.dumps({"status": "FROZEN_NOT_APPROVED", "revision": args.revision,
                          "packet_digest": manifest["packet_digest"], "implementation_authorized": False}, indent=2))
        return 0
    except (InvalidPlan, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "NEEDS_WORK", "errors": [str(exc)], "implementation_authorized": False}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
