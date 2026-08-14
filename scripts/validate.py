#!/usr/bin/env python3
"""Validate the public Trotter profile distribution and pick archive."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError

from package_contract import build_pick_index

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


def package_entries() -> list[tuple[Path, str | None]]:
    """List package paths with staged Git modes when an index is available."""
    try:
        cached = subprocess.run(
            ["git", "ls-files", "--cached", "--stage", "-z"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return sorted(
            (path, None)
            for path in ROOT.rglob("*")
            if ".git" not in path.parts and "__pycache__" not in path.parts
        )
    entries: dict[Path, str | None] = {}
    for raw in cached.stdout.split(b"\0"):
        if not raw:
            continue
        metadata, encoded_path = raw.split(b"\t", 1)
        mode = metadata.split(b" ", 1)[0].decode("ascii")
        entries[ROOT / encoded_path.decode("utf-8")] = mode
    for raw in untracked.stdout.split(b"\0"):
        if raw:
            entries.setdefault(ROOT / raw.decode("utf-8"), None)
    return sorted(entries.items())


def validate_manifest() -> None:
    path = ROOT / "distribution.yaml"
    if not path.is_file():
        fail("missing distribution.yaml")
        return
    try:
        manifest = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
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
    skills = sorted(ROOT.glob("skills/**/SKILL.md"))
    expected = ROOT / "skills" / "horse-racing" / "trotter-handicapping" / "SKILL.md"
    if skills != [expected]:
        rendered = ", ".join(path.relative_to(ROOT).as_posix() for path in skills) or "none"
        fail(
            "expected exactly one skill at "
            "skills/horse-racing/trotter-handicapping/SKILL.md; found " + rendered
        )
    if expected not in skills:
        return 0
    if expected.is_symlink():
        fail(f"{expected.relative_to(ROOT)}: skill file may not be a symlink")
        return 0
    content = expected.read_text(encoding="utf-8")
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
        if not frontmatter.get(field):
            fail(f"{expected.relative_to(ROOT)}: missing {field} frontmatter")
    for ref in ("race-shape-framework.md", "drf-classic-pp-guide.md"):
        if not (expected.parent / "references" / ref).is_file():
            fail(f"{expected.relative_to(ROOT)}: missing reference {ref}")
    return 1


def validate_pick_hashes() -> int:
    directory = ROOT / "picks" / "full-card"
    cards = sorted(directory.glob("*-full-card.md"))
    sidecars = sorted(directory.glob("*-full-card.md.sha256"))
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
    if directory.is_dir():
        for entry in sorted(directory.iterdir()):
            if entry not in expected_entries:
                fail(f"{entry.relative_to(ROOT)}: unexpected full-card archive entry")

    for card in cards:
        sidecar = card.with_name(card.name + ".sha256")
        if card.is_symlink():
            fail(f"{card.relative_to(ROOT)}: full-card file may not be a symlink")
            continue
        if not sidecar.is_file() or sidecar.is_symlink():
            continue
        line = sidecar.read_text(encoding="utf-8").strip()
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
        actual_hash = hashlib.sha256(card.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            fail(f"{sidecar.relative_to(ROOT)}: hash mismatch")
        content = card.read_text(encoding="utf-8")
        for marker in ("Primary win", "Alternative / value", "Safest show"):
            if marker not in content:
                fail(f"{card.relative_to(ROOT)}: missing role {marker}")
    index = ROOT / "picks" / "README.md"
    expected_index = build_pick_index([card.name for card in cards])
    if not index.is_file() or index.read_bytes() != expected_index:
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
        "GitHub token": re.compile(r"gh[opsu]_[A-Za-z0-9]{20,}"),
        "OpenAI key": re.compile("sk" + r"-[A-Za-z0-9_-]{20,}"),
        "AWS access key": re.compile(r"A(?:KIA|SIA)[A-Z0-9]{16}"),
        "credential assignment": re.compile(
            r"(?i)(api[_-]?key|access[_-]?token|client[_-]?secret|password|passwd)"
            r"\s*[=:]\s*[\"']?[A-Za-z0-9_./+-]{12,}"
        ),
        "private key block": re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
        "absolute macOS home": re.compile("/" + "Users/" + r"[^/\s`]+/"),
        "absolute Windows home": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\"),
    }
    for path, git_mode in package_entries():
        relative = path.relative_to(ROOT)
        if git_mode is not None and git_mode not in {"100644", "100755"}:
            fail(f"{relative}: forbidden staged Git mode {git_mode}; expected regular file")
            continue
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
            payload = path.read_bytes()
            if b"\0" in payload:
                fail(f"{relative}: binary NUL byte in text package file")
                continue
            content = payload.decode("utf-8")
        except (OSError, UnicodeError) as exc:
            fail(f"{relative}: unreadable non-UTF-8 package file: {exc}")
            continue
        for label, pattern in patterns.items():
            if pattern.search(content):
                fail(f"{relative}: possible {label}")


def main() -> int:
    validate_manifest()
    skill_count = validate_skill()
    card_count = validate_pick_hashes()
    validate_public_boundary()

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
