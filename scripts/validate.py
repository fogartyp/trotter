#!/usr/bin/env python3
"""Validate the public Trotter profile distribution and pick archive."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError

from package_contract import build_pick_index, parse_card_name

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []
EXPECTED_MANIFEST: dict[str, Any] = {
    "name": "trotter",
    "version": "0.1.0",
    "description": "Patrick Fogarty's evidence-first thoroughbred handicapping partner",
    "hermes_requires": ">=0.20.0",
    "author": "Patrick Fogarty + Trotter",
    "license": "MIT",
    "distribution_owned": ["SOUL.md", "profile.yaml", "skills/", "distribution.yaml"],
}
ALLOWED_TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".txt", ".sha256"}
ALLOWED_EXTENSIONLESS = {"LICENSE", ".gitignore"}
FORBIDDEN_EXACT_NAMES = {
    ".env",
    "config.yaml",
    "auth.json",
    "state.db",
    "state.db-shm",
    "state.db-wal",
    "user.md",
    "projects.db",
    "gateway_state.json",
    "processes.json",
}
FORBIDDEN_SUFFIXES = {
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".crt",
    ".cer",
    ".jsonl",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".log",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".bin",
    ".wasm",
    ".zip",
    ".tar",
    ".gz",
    ".tgz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
}
FORBIDDEN_MULTI_SUFFIXES = (".tar.gz", ".tar.bz2", ".tar.xz")


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def construct_unique_mapping(
    loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    if not isinstance(node, yaml.MappingNode):
        raise ConstructorError(None, None, "expected a mapping node", node.start_mark)
    seen: set[Any] = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in seen
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key: {key!r}",
                key_node.start_mark,
            )
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_unique_mapping
)


def fail(message: str) -> None:
    ERRORS.append(message)


_INDEX_UNSET = object()
_INDEX_CACHE: list[tuple[Path, str, str, str]] | None | object = _INDEX_UNSET


class PackageReadError(RuntimeError):
    """Raised after an authoritative package read has already been reported."""


def git_metadata_present() -> bool:
    if os.environ.get("GIT_DIR") or os.environ.get("GIT_WORK_TREE"):
        return True
    return any(
        (directory / ".git").exists() or (directory / ".git").is_symlink()
        for directory in (ROOT, *ROOT.parents)
    )


def git_index_records() -> list[tuple[Path, str, str, str]] | None:
    """Return all index records without collapsing unmerged stages."""
    global _INDEX_CACHE
    if _INDEX_CACHE is not _INDEX_UNSET:
        return _INDEX_CACHE  # type: ignore[return-value]
    try:
        worktree = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except FileNotFoundError:
        fail("Git index validation failed: git executable is unavailable")
        _INDEX_CACHE = []
        return []
    if worktree.returncode != 0 or worktree.stdout.strip() != "true":
        if git_metadata_present():
            fail(
                "Git repository detection failed while Git metadata is present "
                f"(exit {worktree.returncode})"
            )
            _INDEX_CACHE = []
            return []
        _INDEX_CACHE = None
        return None
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--stage", "-z"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        fail(f"Git index validation failed: {exc}")
        _INDEX_CACHE = []
        return []
    records: list[tuple[Path, str, str, str]] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        metadata, encoded_path = raw.split(b"\t", 1)
        mode, object_id, stage = metadata.decode("ascii").split(" ")
        records.append((ROOT / encoded_path.decode("utf-8"), mode, object_id, stage))
    _INDEX_CACHE = records
    return records


def stage_zero_entries() -> dict[Path, tuple[str, str]] | None:
    records = git_index_records()
    if records is None:
        return None
    return {
        path: (mode, object_id)
        for path, mode, object_id, stage in records
        if stage == "0"
    }


def authoritative_paths() -> list[Path]:
    """Return exactly the regular-file paths represented by the package snapshot."""
    entries = stage_zero_entries()
    if entries is not None:
        return sorted(path for path, (mode, _object_id) in entries.items() if mode in {"100644", "100755"})
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
    )


def package_has_file(path: Path) -> bool:
    entries = stage_zero_entries()
    if entries is not None:
        entry = entries.get(path)
        return entry is not None and entry[0] in {"100644", "100755"}
    return path.is_file() and not path.is_symlink()


def package_bytes(path: Path, object_id: str | None = None) -> bytes:
    """Read an explicit indexed blob or an authoritative package file."""
    if object_id is None:
        entries = stage_zero_entries()
        if entries is not None:
            entry = entries.get(path)
            if entry is None or entry[0] not in {"100644", "100755"}:
                raise FileNotFoundError(path)
            object_id = entry[1]
    if object_id is not None:
        try:
            return subprocess.run(
                ["git", "cat-file", "blob", object_id],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            ).stdout
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            fail(f"Git blob read failed for {path.relative_to(ROOT)}: {exc}")
            raise PackageReadError(path) from exc
    return path.read_bytes()


def package_text(path: Path) -> str:
    return package_bytes(path).decode("utf-8")


def package_entries() -> list[tuple[Path, str | None, str | None, str | None, bool]]:
    """Return indexed records plus untracked files for extra boundary scanning."""
    records = git_index_records()
    if records is None:
        return sorted(
            (path, None, None, None, False)
            for path in ROOT.rglob("*")
            if ".git" not in path.parts and "__pycache__" not in path.parts
        )
    indexed = [(path, mode, object_id, stage, True) for path, mode, object_id, stage in records]
    try:
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        fail("Git untracked-file scan failed")
        return sorted(indexed)
    extras: list[tuple[Path, None, None, None, bool]] = []
    for raw in untracked.stdout.split(b"\0"):
        if not raw:
            continue
        path = ROOT / raw.decode("utf-8")
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        extras.append((path, None, None, None, False))
    return sorted(indexed + extras)


def validate_manifest() -> None:
    path = ROOT / "distribution.yaml"
    if not package_has_file(path):
        fail("missing distribution.yaml")
        return
    try:
        manifest = yaml.load(package_text(path), Loader=UniqueKeyLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        fail(f"distribution.yaml: invalid YAML: {exc}")
        return
    if not isinstance(manifest, dict):
        fail("distribution.yaml: root must be a mapping")
        return
    for key, expected in EXPECTED_MANIFEST.items():
        actual = manifest.get(key)
        if actual != expected:
            qualifier = " exactly" if key == "distribution_owned" else ""
            fail(
                f"distribution.yaml: {key} must equal{qualifier} {expected!r}; got {actual!r}"
            )
    extras = sorted(set(manifest) - set(EXPECTED_MANIFEST))
    if extras:
        fail(f"distribution.yaml: unexpected keys: {', '.join(extras)}")


def validate_skill() -> int:
    skill_root = ROOT / "skills"
    skills = sorted(
        path
        for path in authoritative_paths()
        if path.name == "SKILL.md" and path.is_relative_to(skill_root)
    )
    expected = ROOT / "skills" / "horse-racing" / "trotter-handicapping" / "SKILL.md"
    if skills != [expected]:
        rendered = ", ".join(path.relative_to(ROOT).as_posix() for path in skills) or "none"
        fail(
            "expected exactly one skill at "
            "skills/horse-racing/trotter-handicapping/SKILL.md; found " + rendered
        )
    if expected not in skills:
        return 0

    content = package_text(expected)
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", content, re.DOTALL)
    if not match:
        fail(f"{expected.relative_to(ROOT)}: missing delimiter-only YAML frontmatter")
        return 1
    try:
        frontmatter = yaml.load(match.group(1), Loader=UniqueKeyLoader)
    except yaml.YAMLError as exc:
        fail(f"{expected.relative_to(ROOT)}: invalid frontmatter: {exc}")
        return 1
    if not isinstance(frontmatter, dict):
        fail(f"{expected.relative_to(ROOT)}: frontmatter must be a mapping")
        return 1
    for field in ("name", "description", "version"):
        if not isinstance(frontmatter.get(field), str) or not frontmatter[field].strip():
            fail(f"{expected.relative_to(ROOT)}: {field} must be a non-empty scalar string")
    if frontmatter.get("name") != "trotter-handicapping":
        fail(
            f"{expected.relative_to(ROOT)}: name must equal 'trotter-handicapping'; "
            f"got {frontmatter.get('name')!r}"
        )
    for ref in ("race-shape-framework.md", "drf-classic-pp-guide.md"):
        if not package_has_file(expected.parent / "references" / ref):
            fail(f"{expected.relative_to(ROOT)}: missing reference {ref}")
    return 1


def validate_pick_hashes() -> int:
    directory = ROOT / "picks" / "full-card"
    archive_entries = {path for path in authoritative_paths() if path.parent == directory}
    cards = sorted(
        path for path in archive_entries if path.name.endswith("-full-card.md")
    )
    sidecars = sorted(
        path for path in archive_entries if path.name.endswith("-full-card.md.sha256")
    )
    if not cards:
        fail("no full-card pick files found")
        return 0

    expected_sidecars = {card.with_name(card.name + ".sha256") for card in cards}
    actual_sidecars = set(sidecars)
    for missing in sorted(expected_sidecars - actual_sidecars):
        fail(f"{missing.relative_to(ROOT)}: missing sidecar for {missing.name.removesuffix('.sha256')}")
    for orphan in sorted(actual_sidecars - expected_sidecars):
        fail(f"{orphan.relative_to(ROOT)}: orphan sidecar has no same-basename full card")

    expected_entries = set(cards) | expected_sidecars
    for entry in sorted(archive_entries):
        if entry not in expected_entries:
            fail(f"{entry.relative_to(ROOT)}: unexpected full-card archive entry")

    for card in cards:
        try:
            parse_card_name(card.name)
        except (ValueError, TypeError) as exc:
            fail(f"{card.relative_to(ROOT)}: invalid filename: {exc}")
        sidecar = card.with_name(card.name + ".sha256")
        if not package_has_file(sidecar):
            continue
        line = package_text(sidecar).strip()
        match = re.fullmatch(r"([0-9a-f]{64})\s+([^\s]+)", line)
        if not match:
            fail(f"{sidecar.relative_to(ROOT)}: malformed sidecar")
            continue
        expected_hash, declared_target = match.groups()
        required_target = f"full-card/{card.name}"
        if declared_target != required_target:
            fail(
                f"{sidecar.relative_to(ROOT)}: must target exactly {required_target}; got {declared_target}"
            )
            continue
        actual_hash = hashlib.sha256(package_bytes(card)).hexdigest()
        if actual_hash != expected_hash:
            fail(f"{sidecar.relative_to(ROOT)}: hash mismatch")
        content = package_text(card)
        role_markers = {
            "Primary win": ("Primary win",),
            "Alternative / value": ("Alternative / value", "Alternative/value"),
            "Safest show": ("Safest show",),
        }
        for role, markers in role_markers.items():
            if not any(marker in content for marker in markers):
                fail(f"{card.relative_to(ROOT)}: missing role {role}")
    index = ROOT / "picks" / "README.md"
    try:
        expected_index = build_pick_index([card.name for card in cards])
    except (ValueError, TypeError):
        expected_index = None
    if expected_index is not None and (
        not package_has_file(index) or package_bytes(index) != expected_index
    ):
        fail("picks/README.md: stale or inconsistent with full-card archive")
    return len(cards)


def sensitive_reason(path: Path) -> str | None:
    lower = path.name.lower()
    if lower in FORBIDDEN_EXACT_NAMES or lower.startswith(".env."):
        return "private/runtime filename"
    if any(lower.endswith(suffix) for suffix in FORBIDDEN_MULTI_SUFFIXES):
        return "archive"
    if any(lower.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
        return "private/runtime/binary suffix"
    if re.search(r"\.(?:sqlite|sqlite3|db)(?:-|$)", lower):
        return "SQLite/runtime variant"
    if path.suffix.lower() not in ALLOWED_TEXT_SUFFIXES and path.name not in ALLOWED_EXTENSIONLESS:
        return "unknown package extension"
    return None


def validate_public_boundary() -> None:
    patterns = {
        "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
        "GitHub fine-grained token": re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
        "OpenAI key": re.compile("sk" + r"-[A-Za-z0-9_-]{20,}"),
        "AWS access key": re.compile(r"A(?:KIA|SIA)[A-Z0-9]{16}"),
        "AWS secret": re.compile(
            r"(?i)[\"']?(?:aws_)?secret(?:_?access)?_?key[\"']?"
            r"\s*[=:]\s*[\"']?[A-Za-z0-9/+=]{40}"
        ),
        "Slack token": re.compile(r"x(?:ox[a-z]|app|wfp)-[A-Za-z0-9-]{10,}"),
        "credential assignment": re.compile(
            r"(?i)[\"']?(api[_-]?key|access[_-]?token|client[_-]?secret|password|passwd)"
            r"[\"']?\s*[=:]\s*[\"']?[A-Za-z0-9_./+-]{12,}"
        ),
        "private key block": re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
        "absolute macOS home": re.compile("/" + "Users/" + r"[^/\s`]+/"),
        "absolute Windows home": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\"),
    }
    for path, git_mode, object_id, stage, indexed in package_entries():
        relative = path.relative_to(ROOT)
        if indexed and stage != "0":
            fail(f"{relative}: unmerged index stage {stage} is not allowed")
            continue
        if indexed and git_mode not in {"100644", "100755"}:
            fail(f"{relative}: forbidden staged Git mode {git_mode}; expected regular file")
            continue
        if not indexed:
            if path.is_symlink():
                fail(f"{relative}: symlink is not allowed in the public package")
                continue
            if path.is_dir():
                continue
            if not path.is_file():
                fail(f"{relative}: non-regular package entry")
                continue
        reason = sensitive_reason(path)
        if reason:
            fail(f"{relative}: forbidden {reason}")
            continue
        try:
            payload = package_bytes(path, object_id) if indexed else path.read_bytes()
            if b"\0" in payload:
                fail(f"{relative}: binary NUL byte in text package file")
                continue
            content = payload.decode("utf-8")
        except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
            fail(f"{relative}: unreadable non-UTF-8 package file: {exc}")
            continue
        for label, pattern in patterns.items():
            if pattern.search(content):
                fail(f"{relative}: possible {label}")


def main() -> int:
    skill_count = 0
    card_count = 0
    try:
        validate_manifest()
        skill_count = validate_skill()
        card_count = validate_pick_hashes()
        validate_public_boundary()
    except PackageReadError:
        pass

    if ERRORS:
        print(f"Validation failed with {len(ERRORS)} error(s):")
        for error in ERRORS:
            print(f"  - {error}")
        return 1
    print(
        f"Validation passed: 1 profile manifest, {skill_count} skill, "
        f"{card_count} hash-locked full-card pick files, no forbidden private artifacts."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
