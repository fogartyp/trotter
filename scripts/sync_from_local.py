#!/usr/bin/env python3
"""Sync the public, allowlisted parts of a local Trotter setup."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

from package_contract import build_pick_index

REPO = Path(__file__).resolve().parents[1]
SKILL_TARGET = REPO / "skills" / "horse-racing" / "trotter-handicapping"
PICKS_TARGET = REPO / "picks" / "full-card"
REPOSITORY_MAINTAINED = {SKILL_TARGET / "agents" / "openai.yaml"}


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def assert_safe_source(source: Path, approved_root: Path) -> None:
    """Reject symlinks and sources escaping their approved root."""
    root_absolute = approved_root.expanduser().absolute()
    if root_absolute.is_symlink():
        raise ValueError(f"Approved source root is a symlink: {approved_root}")
    root_resolved = root_absolute.resolve(strict=True)
    source_absolute = source.expanduser().absolute()
    if not is_within(source_absolute, root_absolute):
        raise ValueError(f"Source is outside approved root {approved_root}: {source}")

    relative = source_absolute.relative_to(root_absolute)
    cursor = root_absolute
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"Source symlink is not allowed: {cursor}")

    resolved = source_absolute.resolve(strict=True)
    if not is_within(resolved, root_resolved):
        raise ValueError(f"Source resolves outside approved root {approved_root}: {source}")
    if not resolved.is_file():
        raise FileNotFoundError(source)


def assert_safe_target(target: Path) -> None:
    """Never follow a repository symlink while reading or writing output."""
    repo_absolute = REPO.absolute()
    target_absolute = target.absolute()
    if not is_within(target_absolute, repo_absolute):
        raise ValueError(f"Target is outside repository: {target}")
    cursor = repo_absolute
    for part in target_absolute.relative_to(repo_absolute).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"Repository target symlink is not allowed: {cursor}")


def public_payload(source: Path, target: Path) -> bytes:
    """Read a source file and normalize packaged skill Markdown."""
    payload = source.read_bytes()
    if "skills" in target.parts and target.suffix == ".md":
        text = payload.decode("utf-8")
        payload = ("\n".join(line.rstrip() for line in text.splitlines()) + "\n").encode("utf-8")
    return payload


def existing_skill_dir(profile_root: Path) -> Path:
    candidates = [
        profile_root / "skills" / "trotter-handicapping",
        profile_root / "skills" / "horse-racing" / "trotter-handicapping",
    ]
    for candidate in candidates:
        skill_md = candidate / "SKILL.md"
        if skill_md.exists() or skill_md.is_symlink():
            assert_safe_source(skill_md, profile_root)
            return candidate
    raise FileNotFoundError(
        "Could not find trotter-handicapping under " + str(profile_root / "skills")
    )


def workspace_root() -> Path:
    configured = os.environ.get("TROTTER_WORKSPACE")
    if configured:
        return Path(configured).expanduser().absolute()
    sibling = REPO.parent / "trotter-handicapping"
    if sibling.is_dir():
        return sibling.absolute()
    return (Path.home() / "trotter-handicapping").absolute()


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def managed_stale_paths(expected_targets: set[Path]) -> list[Path]:
    """Return unexpected generated files without touching repo-maintained metadata."""
    allowed = expected_targets | REPOSITORY_MAINTAINED
    stale: list[Path] = []
    for root in (SKILL_TARGET, PICKS_TARGET):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_dir() and not path.is_symlink():
                continue
            if path not in allowed:
                stale.append(path)
    return sorted(stale)


def prune_empty_managed_dirs() -> None:
    for root in (SKILL_TARGET, PICKS_TARGET):
        if not root.exists():
            continue
        directories = [path for path in root.rglob("*") if path.is_dir() and not path.is_symlink()]
        for directory in sorted(directories, key=lambda path: len(path.parts), reverse=True):
            if directory == SKILL_TARGET / "agents":
                continue
            try:
                directory.rmdir()
            except OSError:
                pass


def atomic_write(target: Path, payload: bytes) -> None:
    """Replace one file without exposing a partially written target."""
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temp_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def snapshot_outputs(backup_root: Path) -> list[tuple[Path, Path | None]]:
    """Capture every sync-owned output so a failed mutation can roll back."""
    snapshots: list[tuple[Path, Path | None]] = []
    for index, original in enumerate(
        (REPO / "SOUL.md", REPO / "profile.yaml", SKILL_TARGET, REPO / "picks")
    ):
        if not original.exists() and not original.is_symlink():
            snapshots.append((original, None))
            continue
        backup = backup_root / str(index)
        if original.is_dir() and not original.is_symlink():
            shutil.copytree(original, backup, symlinks=True)
        else:
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, backup, follow_symlinks=False)
        snapshots.append((original, backup))
    return snapshots


def restore_outputs(snapshots: list[tuple[Path, Path | None]]) -> None:
    for original, backup in snapshots:
        if original.exists() or original.is_symlink():
            remove_path(original)
        if backup is None:
            continue
        if backup.is_dir() and not backup.is_symlink():
            shutil.copytree(backup, original, symlinks=True)
        else:
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, original, follow_symlinks=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    args = parser.parse_args()

    profile_root = Path(
        os.environ.get("HERMES_HOME", str(Path.home() / ".hermes" / "profiles" / "trotter"))
    ).expanduser().absolute()
    workspace = workspace_root()
    if profile_root.is_symlink() or workspace.is_symlink():
        raise ValueError("Approved profile and workspace roots may not be symlinks")
    profile_root.resolve(strict=True)
    workspace.resolve(strict=True)
    skill = existing_skill_dir(profile_root)

    pairs: list[tuple[Path, Path, Path]] = [
        (profile_root / "SOUL.md", REPO / "SOUL.md", profile_root),
        (profile_root / "profile.yaml", REPO / "profile.yaml", profile_root),
        (skill / "SKILL.md", SKILL_TARGET / "SKILL.md", profile_root),
    ]
    references = skill / "references"
    if references.is_symlink():
        resolved_references = references.resolve(strict=True)
        if not is_within(resolved_references, profile_root.resolve(strict=True)):
            raise ValueError(
                f"Source resolves outside approved root {profile_root}: {references}"
            )
        raise ValueError(f"Source symlink is not allowed: {references}")
    for ref in sorted(references.glob("*.md")):
        pairs.append((ref, SKILL_TARGET / "references" / ref.name, profile_root))

    full_card = workspace / "full-card"
    if full_card.is_symlink():
        raise ValueError(f"Source symlink is not allowed: {full_card}")
    cards = sorted(full_card.glob("*-full-card.md"))
    if not cards:
        raise FileNotFoundError(f"No *-full-card.md files found in {full_card}")
    for card in cards:
        pairs.append((card, PICKS_TARGET / card.name, workspace))
        sidecar = card.with_name(card.name + ".sha256")
        if not sidecar.exists() and not sidecar.is_symlink():
            raise FileNotFoundError(f"Missing integrity sidecar: {sidecar}")
        pairs.append((sidecar, PICKS_TARGET / sidecar.name, workspace))

    for source, target, approved_root in pairs:
        assert_safe_source(source, approved_root)
        assert_safe_target(target)

    index_target = REPO / "picks" / "README.md"
    assert_safe_target(index_target)

    # Validate and normalize every source before touching repository output.
    payloads = [
        (target, public_payload(source, target)) for source, target, _ in pairs
    ]
    payloads.append((index_target, build_pick_index([card.name for card in cards])))

    expected_targets = {target for _, target, _ in pairs}
    stale = managed_stale_paths(expected_targets)
    drift = [path.relative_to(REPO).as_posix() for path in stale]
    changed_targets: list[tuple[Path, bytes]] = []
    for target, payload in payloads:
        if not target.is_file() or target.read_bytes() != payload:
            drift.append(target.relative_to(REPO).as_posix())
            changed_targets.append((target, payload))

    if args.check:
        if drift:
            print("Out of sync:")
            for path in sorted(set(drift)):
                print(f"  {path}")
            return 1
        print(f"Sync check passed: {len(pairs)} source artifacts and picks index match.")
        return 0

    changed = [path.relative_to(REPO).as_posix() for path in stale]
    changed.extend(target.relative_to(REPO).as_posix() for target, _ in changed_targets)
    with tempfile.TemporaryDirectory(prefix="trotter-sync-backup-") as backup:
        snapshots = snapshot_outputs(Path(backup))
        try:
            for path in stale:
                remove_path(path)
            for target, payload in changed_targets:
                atomic_write(target, payload)
            prune_empty_managed_dirs()
        except Exception:
            restore_outputs(snapshots)
            raise

    print(f"Sync complete: {len(changed)} file(s) updated; {len(cards)} card(s) indexed.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (FileNotFoundError, OSError, UnicodeError, ValueError) as exc:
        print(f"Sync failed: {exc}", file=sys.stderr)
        sys.exit(1)
