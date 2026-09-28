#!/usr/bin/env python3
"""Audit an explicitly mapped, possibly flattened source bundle. Never import approval.

No network, Git, model calls or product writes. Paths mentioned by documents are
resolved in a virtual project namespace and are NEVER opened unless explicitly
included in the input map. This is a simple inline-link audit, not CommonMark.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from common import InvalidPlan, MAX_FILE_BYTES, digest, load_json, need, safe_path, string_list, text

LINK = re.compile(r'\[[^\]\n]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+"[^"]*")?\)')
REFERENCE_STYLE = re.compile(r'(?m)^\s*\[[^\]]+\]:|\[[^\]\n]+\]\[[^\]\n]*\]')


def logical_path(value: Any) -> str:
    value = text(value, "logical path")
    need(not value.startswith("/") and "\\" not in value and "\x00" not in value,
         "Logical paths must be project-relative POSIX paths")
    need(posixpath.normpath(value) == value and value not in {".", ".."}
         and not value.startswith("../"), "Logical paths must be canonical and remain inside the project")
    return value


def visible_markdown(value: str) -> str:
    # Keep newlines so recorded locations still refer to the original uploaded bytes.
    def blank(match: re.Match[str]) -> str:
        return "\n" * match.group(0).count("\n")
    value = re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1\s*$", blank, value)
    return re.sub(r"(?s)<!--.*?-->", blank, value)


def audit(root: Path, mapping: dict[str, Any]) -> dict[str, Any]:
    need(type(mapping.get("schema_version")) is int and mapping["schema_version"] == 1,
         "Unsupported source-map schema")
    need(root.is_dir() and not root.is_symlink(), "Source root must be an ordinary directory")
    rows = mapping.get("files")
    need(isinstance(rows, list) and bool(rows), "files must be a nonempty array")
    captured: dict[str, bytes] = {}
    records: list[dict[str, Any]] = []
    local_names: set[str] = set()
    for row in rows:
        need(isinstance(row, dict), "Source-map file must be an object")
        name = logical_path(row.get("logical_path"))
        need(name not in captured, f"Duplicate logical path: {name}")
        local = text(row.get("local_path"), "local_path")
        source = safe_path(root, local)
        need(source.is_file(), f"Mapped input is missing: {local}")
        resolved = str(source.resolve())
        need(resolved not in local_names, "One input may not masquerade as multiple original paths")
        local_names.add(resolved)
        need(source.stat().st_size <= MAX_FILE_BYTES, f"Input too large: {local}")
        data = source.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if "expected_sha256" in row:
            need(row["expected_sha256"] == sha, f"Mapped input changed: {local}")
        captured[name] = data
        records.append({"logical_path": name, "local_path": local, "sha256": sha, "bytes": len(data)})
    entrypoint = logical_path(mapping.get("entrypoint"))
    need(entrypoint in captured, "Entrypoint must be an explicitly mapped file")
    active = set(string_list(mapping.get("active_documents"), "active_documents", True))
    need(entrypoint in active and active <= set(captured), "Active documents must include the mapped entrypoint")
    required = string_list(mapping.get("required_documents", []), "required_documents")
    for name in required:
        logical_path(name)
    links: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []
    external_count = 0
    for name, data in captured.items():
        if not name.endswith(".md"):
            continue
        source = visible_markdown(data.decode("utf-8"))
        for match in REFERENCE_STYLE.finditer(source):
            unsupported.append({"source": name, "line": source[:match.start()].count("\n") + 1,
                                "kind": "reference-style-link", "active": name in active})
        for match in LINK.finditer(source):
            target = match.group(1) or match.group(2)
            parts = urlsplit(target)
            if parts.scheme or parts.netloc:
                external_count += 1
                continue
            raw_path = unquote(parts.path)
            if raw_path.startswith("/") or "\\" in raw_path:
                dest = raw_path
                state = "unmapped_absolute_path"
            else:
                dest = posixpath.normpath(posixpath.join(posixpath.dirname(name), raw_path)) if raw_path else name
                state = "present" if dest in captured else "not_supplied"
            links.append({"source": name, "line": source[:match.start()].count("\n") + 1,
                          "target": target, "logical_target": dest, "status": state,
                          "active": name in active, "anchor_checked": False})
    missing = sorted({link["logical_target"] for link in links if link["status"] != "present"})
    missing_active = sorted({link["logical_target"] for link in links
                             if link["active"] and link["status"] != "present"})
    missing_required = sorted(set(required) - set(captured))
    hashes = {row["logical_path"]: row["sha256"] for row in records}
    partial = bool(missing or missing_required or unsupported)
    return {
        "schema_version": 1,
        "status": "PARTIAL_SOURCE_BUNDLE" if partial else "SOURCE_LINKS_RESOLVED",
        "entrypoint": entrypoint,
        "files": sorted(records, key=lambda row: row["logical_path"]),
        "active_documents": sorted(active),
        "uploaded_content_digest": digest(hashes),
        "summary": {"supplied_files": len(records), "active_documents": len(active),
                    "local_link_occurrences": len(links), "unique_unresolved_targets": len(missing),
                    "active_unresolved_targets": len(missing_active),
                    "required_documents_missing": len(missing_required), "external_links_not_fetched": external_count},
        "missing_required_documents": missing_required,
        "unresolved_targets": missing,
        "active_unresolved_targets": missing_active,
        "links": links,
        "unsupported_syntax": unsupported,
        "review_authenticity": "not_verified",
        "implementation_authorized": False,
        "limitations": [
            "Hashes identify supplied bytes, not the original review manifest or repository revision.",
            "Missing targets mean not supplied here, not absent in the original repository.",
            "Only simple inline Markdown links are inspected; anchors and bare/code-span paths are not validated.",
            "Reference-style syntax is flagged rather than silently treated as complete.",
            "Active-document selection is explicit metadata, not inferred authority from filenames or timestamps.",
            "Archived handoffs, user quotations and verdicts are reported evidence, not fresh execution authorization."
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Directory containing the explicitly mapped uploads")
    parser.add_argument("--map", required=True, type=Path, dest="mapping", help="Source-map JSON; no automatic path discovery")
    args = parser.parse_args()
    try:
        result = audit(args.root, load_json(args.mapping))
        code = 1 if result["status"] == "PARTIAL_SOURCE_BUNDLE" else 0
    except (InvalidPlan, OSError, ValueError, TypeError, KeyError) as exc:
        result = {"status": "INVALID_SOURCE_MAP", "errors": [str(exc)], "implementation_authorized": False}
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
