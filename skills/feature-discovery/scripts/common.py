"""Local artifact integrity helpers. No network, subprocesses, or model calls."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

MAX_FILE_BYTES = 5 * 1024 * 1024
REQUIRED_FILES = {"plan.json", "brief.md", "analysis.md", "implementation.md", "tests.md"}
REVISION = re.compile(r"r[0-9]{2,}")


class InvalidPlan(ValueError):
    """A malformed or inconsistent planning artifact."""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidPlan(message)


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        need(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    need(path.is_file() and not path.is_symlink(), f"Missing or symlinked JSON: {path}")
    need(path.stat().st_size <= MAX_FILE_BYTES, f"JSON is too large: {path}")
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    need(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def text(value: Any, label: str) -> str:
    need(isinstance(value, str) and bool(value.strip()), f"{label}: nonempty string required")
    need(not re.search(r"\b(TODO|TBD|REPLACE_ME)\b|\{\{", value), f"{label}: unresolved placeholder")
    return value


def string_list(value: Any, label: str, nonempty: bool = False) -> list[str]:
    need(isinstance(value, list), f"{label}: array required")
    need(all(isinstance(x, str) and bool(x.strip()) for x in value), f"{label}: nonempty strings required")
    need(len(value) == len(set(value)), f"{label}: duplicate values")
    need(not nonempty or bool(value), f"{label}: cannot be empty")
    return value


def safe_path(root: Path, relative: str) -> Path:
    need(isinstance(relative, str) and bool(relative), "Empty relative path")
    item = Path(relative)
    need(not item.is_absolute() and ".." not in item.parts and "\\" not in relative,
         f"Unsafe relative path: {relative}")
    target = root / item
    for parent in [target, *target.parents]:
        if parent == root.parent:
            break
        need(not parent.is_symlink(), f"Symlinks are not supported inside artifacts: {parent}")
    need(target.resolve().is_relative_to(root.resolve()), f"Path escapes artifact root: {relative}")
    return target


def file_bytes(root: Path) -> dict[str, bytes]:
    need(root.is_dir() and not root.is_symlink(), f"Missing or symlinked directory: {root}")
    result: dict[str, bytes] = {}
    for item in sorted(root.rglob("*")):
        relative = item.relative_to(root).as_posix()
        safe_path(root, relative)
        if item.is_dir():
            continue
        need(item.is_file(), f"Not a regular file: {relative}")
        need(item.suffix in {".md", ".json", ".txt"}, f"Unsupported packet file type: {relative}")
        need(item.stat().st_size <= MAX_FILE_BYTES, f"Packet file too large: {relative}")
        result[relative] = item.read_bytes()
    need(REQUIRED_FILES <= set(result), f"Missing packet files: {sorted(REQUIRED_FILES - set(result))}")
    return result


def file_hashes(root: Path) -> dict[str, str]:
    return {name: hashlib.sha256(data).hexdigest() for name, data in file_bytes(root).items()}


def verify_snapshot(run: Path, revision: str) -> tuple[dict[str, Any], Path]:
    need(bool(REVISION.fullmatch(revision)), f"Invalid revision: {revision}")
    root = safe_path(run, f"revisions/{revision}")
    manifest = load_json(root / "manifest.json")
    need(manifest.get("schema_version") == 1 and manifest.get("revision") == revision,
         "Manifest version/revision mismatch")
    payload = {k: v for k, v in manifest.items() if k != "packet_digest"}
    need(manifest.get("packet_digest") == digest(payload), "Manifest digest mismatch")
    need(manifest.get("files") == file_hashes(root / "packet"), "Frozen packet was changed, added to, or truncated")
    return manifest, root / "packet"


def markdown_links(root: Path) -> None:
    """Check inline local links and anchors; external URLs are not fetched.

    Deliberately not a CommonMark parser. Use simple inline links in run packets.
    Reference-style links are rejected rather than silently left unchecked.
    """
    def stripped(value: str) -> str:
        return re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1\s*$", "", value)

    def anchors(value: str) -> set[str]:
        found = set(re.findall(r'<a\s+(?:id|name)=[\"\']([^\"\']+)[\"\']', value))
        counts: dict[str, int] = {}
        for heading in re.findall(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", stripped(value)):
            slug = re.sub(r"[^\w\- ]", "", heading.replace("`", "").lower()).replace(" ", "-")
            count = counts.get(slug, 0)
            counts[slug] = count + 1
            found.add(slug if count == 0 else f"{slug}-{count}")
        return found

    for relative, data in file_bytes(root).items():
        if not relative.endswith(".md"):
            continue
        source = stripped(data.decode("utf-8"))
        need(not re.search(r"(?m)^\s*\[[^\]]+\]:|\[[^\]\n]+\]\[[^\]\n]*\]", source),
             f"{relative}: use inline links, not reference-style links")
        for match in re.finditer(r"\[[^\]\n]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+\"[^\"]*\")?\)", source):
            target = match.group(1) or match.group(2)
            parts = urlsplit(target)
            if parts.scheme or parts.netloc:
                need(parts.scheme in {"https", "http", "mailto"} or bool(parts.netloc),
                     f"{relative}: unsupported link scheme: {target}")
                continue
            local = unquote(parts.path)
            candidate = (root / relative).parent / local if local else root / relative
            need(candidate.resolve().is_relative_to(root.resolve()), f"{relative}: link escapes packet: {target}")
            normalized = candidate.resolve().relative_to(root.resolve()).as_posix()
            dest = safe_path(root, normalized)
            need(dest.is_file(), f"{relative}: broken link: {target}")
            if parts.fragment and dest.suffix == ".md":
                need(unquote(parts.fragment) in anchors(dest.read_text(encoding="utf-8")),
                     f"{relative}: missing anchor: {target}")
