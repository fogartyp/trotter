from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))
VALIDATE_SOURCE = SOURCE_ROOT / "scripts" / "validate.py"
SYNC_SOURCE = SOURCE_ROOT / "scripts" / "sync_from_local.py"
CONTRACT_SOURCE = SOURCE_ROOT / "scripts" / "package_contract.py"

MANIFEST_VALUES = {
    "name": "trotter",
    "version": "0.1.0",
    "description": "Patrick Fogarty's evidence-first thoroughbred handicapping partner",
    "hermes_requires": ">=0.20.0",
    "author": "Patrick Fogarty + Trotter",
    "license": "MIT",
}
OWNED_PATHS = ["SOUL.md", "profile.yaml", "skills/", "distribution.yaml"]
CARD_NAME = "2026-08-14-SAR-full-card.md"
CARD_CONTENT = "# Card\n\nPrimary win\nAlternative / value\nSafest show\n"


def manifest_yaml(*, owned: list[str] | None = None) -> str:
    values = MANIFEST_VALUES
    owned = OWNED_PATHS if owned is None else owned
    return textwrap.dedent(
        f"""\
        name: {values['name']}
        version: {values['version']}
        description: {values['description']!r}
        hermes_requires: {values['hermes_requires']!r}
        author: {values['author']}
        license: {values['license']}
        distribution_owned:
        """
    ) + "".join(f"  - {path}\n" for path in owned)


def write_card(root: Path, name: str = CARD_NAME, *, target: str | None = None) -> tuple[Path, Path]:
    card = root / "picks" / "full-card" / name
    card.parent.mkdir(parents=True, exist_ok=True)
    card.write_text(CARD_CONTENT, encoding="utf-8")
    sidecar = card.with_name(card.name + ".sha256")
    target = target if target is not None else f"full-card/{card.name}"
    sidecar.write_text(
        f"{hashlib.sha256(CARD_CONTENT.encode()).hexdigest()}  {target}\n",
        encoding="utf-8",
    )
    return card, sidecar


def make_validation_package(base: Path) -> Path:
    root = base / "package"
    (root / "scripts").mkdir(parents=True)
    shutil.copy2(VALIDATE_SOURCE, root / "scripts" / "validate.py")
    shutil.copy2(CONTRACT_SOURCE, root / "scripts" / "package_contract.py")
    (root / "distribution.yaml").write_text(manifest_yaml(), encoding="utf-8")
    (root / "SOUL.md").write_text("# Soul\n", encoding="utf-8")
    (root / "profile.yaml").write_text("description: Trotter\n", encoding="utf-8")
    skill = root / "skills" / "horse-racing" / "trotter-handicapping"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: trotter-handicapping\ndescription: Test skill\nversion: 1.0.0\n---\n",
        encoding="utf-8",
    )
    for name in ("race-shape-framework.md", "drf-classic-pp-guide.md"):
        (skill / "references" / name).write_text(f"# {name}\n", encoding="utf-8")
    write_card(root)
    from scripts.package_contract import build_pick_index

    (root / "picks" / "README.md").write_bytes(build_pick_index([CARD_NAME]))
    return root


def run_validate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/validate.py"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def make_sync_fixture(base: Path) -> tuple[Path, Path, Path]:
    repo = base / "repo"
    profile = base / "profile"
    workspace = base / "workspace"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy2(SYNC_SOURCE, repo / "scripts" / "sync_from_local.py")
    shutil.copy2(CONTRACT_SOURCE, repo / "scripts" / "package_contract.py")

    skill = profile / "skills" / "trotter-handicapping"
    (skill / "references").mkdir(parents=True)
    (profile / "SOUL.md").write_text("# Soul\n", encoding="utf-8")
    (profile / "profile.yaml").write_text("description: Trotter\n", encoding="utf-8")
    (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    (skill / "references" / "guide.md").write_text("# Guide\n", encoding="utf-8")

    source_card = workspace / "full-card" / CARD_NAME
    source_card.parent.mkdir(parents=True)
    source_card.write_text(CARD_CONTENT, encoding="utf-8")
    source_card.with_name(source_card.name + ".sha256").write_text(
        f"{hashlib.sha256(CARD_CONTENT.encode()).hexdigest()}  full-card/{CARD_NAME}\n",
        encoding="utf-8",
    )

    agent = repo / "skills" / "horse-racing" / "trotter-handicapping" / "agents" / "openai.yaml"
    agent.parent.mkdir(parents=True)
    agent.write_text("interface:\n  display_name: Repository maintained\n", encoding="utf-8")
    return repo, profile, workspace


def run_sync(
    repo: Path, profile: Path, workspace: Path, *, check: bool = False
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({"HERMES_HOME": str(profile), "TROTTER_WORKSPACE": str(workspace)})
    args = [sys.executable, "scripts/sync_from_local.py"]
    if check:
        args.append("--check")
    return subprocess.run(
        args,
        cwd=repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


class SyncSourceSecurityTests(unittest.TestCase):
    def test_rejects_a_source_file_symlink_even_when_target_is_inside_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, profile, workspace = make_sync_fixture(Path(tmp))
            soul = profile / "SOUL.md"
            real = profile / "real-soul.md"
            soul.rename(real)
            soul.symlink_to(real)

            result = run_sync(repo, profile, workspace)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("symlink", result.stdout.lower())

    def test_rejects_a_source_resolving_outside_approved_profile_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo, profile, workspace = make_sync_fixture(base)
            external = base / "external-references"
            external.mkdir()
            (external / "guide.md").write_text("outside\n", encoding="utf-8")
            references = profile / "skills" / "trotter-handicapping" / "references"
            shutil.rmtree(references)
            references.symlink_to(external, target_is_directory=True)

            result = run_sync(repo, profile, workspace)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("outside approved", result.stdout.lower())

    def test_rejects_a_workspace_card_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, profile, workspace = make_sync_fixture(Path(tmp))
            card = workspace / "full-card" / CARD_NAME
            real = workspace / "full-card" / "real-card.md"
            card.rename(real)
            card.symlink_to(real)

            result = run_sync(repo, profile, workspace)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("symlink", result.stdout.lower())


class SyncStaleFileTests(unittest.TestCase):
    def test_check_reports_stale_files_and_sync_removes_them_but_preserves_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, profile, workspace = make_sync_fixture(Path(tmp))
            first = run_sync(repo, profile, workspace)
            self.assertEqual(first.returncode, 0, first.stdout)
            skill = repo / "skills" / "horse-racing" / "trotter-handicapping"
            stale_reference = skill / "references" / "stale.md"
            stale_reference.write_text("stale\n", encoding="utf-8")
            stale_content = skill / "content" / "nested" / "stale.txt"
            stale_content.parent.mkdir(parents=True)
            stale_content.write_text("stale\n", encoding="utf-8")
            stale_pick = repo / "picks" / "full-card" / "stale-full-card.md"
            stale_pick.write_text("stale\n", encoding="utf-8")
            agent = skill / "agents" / "openai.yaml"
            original_agent = agent.read_bytes()

            check = run_sync(repo, profile, workspace, check=True)
            self.assertNotEqual(check.returncode, 0, check.stdout)
            for path in (stale_reference, stale_content, stale_pick):
                self.assertIn(path.relative_to(repo).as_posix(), check.stdout)

            sync = run_sync(repo, profile, workspace)
            self.assertEqual(sync.returncode, 0, sync.stdout)
            for path in (stale_reference, stale_content, stale_pick):
                self.assertFalse(path.exists(), path)
            self.assertEqual(agent.read_bytes(), original_agent)


class SyncAtomicityTests(unittest.TestCase):
    def test_invalid_source_leaves_repository_byte_for_byte_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, profile, workspace = make_sync_fixture(Path(tmp))
            first = run_sync(repo, profile, workspace)
            self.assertEqual(first.returncode, 0, first.stdout)
            stale = repo / "picks" / "full-card" / "stale-full-card.md"
            stale.write_text("must survive a failed sync\n", encoding="utf-8")
            (profile / "SOUL.md").write_text("# Updated soul\n", encoding="utf-8")
            (profile / "skills" / "trotter-handicapping" / "SKILL.md").write_bytes(
                b"\xff\xfeinvalid UTF-8"
            )

            before = {
                path.relative_to(repo).as_posix(): path.read_bytes()
                for path in repo.rglob("*")
                if path.is_file()
            }
            result = run_sync(repo, profile, workspace)
            after = {
                path.relative_to(repo).as_posix(): path.read_bytes()
                for path in repo.rglob("*")
                if path.is_file()
            }

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertEqual(after, before)


class PublicBoundaryTests(unittest.TestCase):
    def test_rejects_all_sensitive_runtime_binary_and_symlink_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = make_validation_package(base)
            offenders = {
                ".env.production": b"TOKEN=secret\n",
                "private.key": b"secret\n",
                "certificate.pem": b"secret\n",
                "backup.tar.gz": b"archive\n",
                "session.jsonl": b'{"role":"user"}\n',
                "state.sqlite3-wal": b"sqlite\n",
                "program.bin": b"\x00\x01binary",
            }
            for name, payload in offenders.items():
                (root / name).write_bytes(payload)
            (root / "linked.txt").symlink_to(base / "outside.txt")

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            for name in [*offenders, "linked.txt"]:
                with self.subTest(name=name):
                    self.assertIn(name, result.stdout)

    def test_rejects_unknown_package_extensions_instead_of_skipping_them(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            (root / "payload.wasm").write_bytes(b"valid-looking bytes")

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("payload.wasm", result.stdout)

    def test_rejects_common_cloud_credentials_and_private_key_headers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            aws_key = "AKIA" + "ABCDEFGHIJKLMNOP"
            private_header = "-----BEGIN OPENSSH " + "PRIVATE KEY-----"
            (root / "notes.txt").write_text(
                f"{aws_key}\n{private_header}\n", encoding="utf-8"
            )

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("AWS", result.stdout)
            self.assertIn("private key", result.stdout.lower())

    def test_rejects_a_staged_gitlink_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            gitlink = root / "vendor"
            gitlink.mkdir()
            subprocess.run(
                [
                    "git",
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    "160000,1111111111111111111111111111111111111111,vendor",
                ],
                cwd=root,
                check=True,
            )

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("vendor", result.stdout)
            self.assertIn("160000", result.stdout)

    def test_scans_staged_blob_instead_of_benign_working_tree_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            note = root / "notes.txt"
            staged_key = "sk" + "-" + "A" * 32
            note.write_text(staged_key + "\n", encoding="utf-8")
            subprocess.run(["git", "add", "notes.txt"], cwd=root, check=True)
            note.write_text("benign working tree text\n", encoding="utf-8")

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("OpenAI", result.stdout)

    def test_scans_staged_blob_when_working_path_becomes_a_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            note = root / "notes.txt"
            note.write_text("sk" + "-" + "A" * 32 + "\n", encoding="utf-8")
            subprocess.run(["git", "add", "notes.txt"], cwd=root, check=True)
            note.unlink()
            note.mkdir()

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("OpenAI", result.stdout)

    def test_rejects_additional_high_confidence_token_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            github = "github" + "_pat_" + "A" * 40
            slack = "xox" + "b-" + "123456789012-" + "A" * 24
            aws_probe = "aws_secret_access_key = " + "A" * 40
            (root / "notes.txt").write_text(
                "\n".join((github, slack, aws_probe)) + "\n", encoding="utf-8"
            )

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            for label in ("GitHub", "Slack", "AWS secret"):
                self.assertIn(label, result.stdout)

    def test_rejects_official_token_prefixes_and_quoted_secret_assignments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            probes = (
                "gh" + "r_" + "A" * 40,
                "gh" + "s_123456_" + "A" * 24,
                "x" + "app-1-" + "A" * 32,
                "x" + "wfp-" + "A" * 32,
                "SecretAccessKey = " + "A" * 40,
                '"aws_secret_access_key": "' + "A" * 40 + '"',
                '"api_key": "' + "A" * 32 + '"',
            )
            (root / "notes.txt").write_text("\n".join(probes) + "\n", encoding="utf-8")

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            for label in ("GitHub", "Slack", "AWS secret", "credential assignment"):
                self.assertIn(label, result.stdout)

    def test_rejects_any_unmerged_index_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            secret = subprocess.run(
                ["git", "hash-object", "-w", "--stdin"],
                cwd=root,
                input="sk" + "-" + "A" * 32 + "\n",
                text=True,
                stdout=subprocess.PIPE,
                check=True,
            ).stdout.strip()
            benign = subprocess.run(
                ["git", "hash-object", "-w", "--stdin"],
                cwd=root,
                input="benign\n",
                text=True,
                stdout=subprocess.PIPE,
                check=True,
            ).stdout.strip()
            subprocess.run(
                ["git", "update-index", "--index-info"],
                cwd=root,
                input=(
                    f"100644 {secret} 2\tnotes.txt\n"
                    f"100644 {benign} 3\tnotes.txt\n"
                ),
                text=True,
                check=True,
            )

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("unmerged", result.stdout.lower())
            self.assertIn("notes.txt", result.stdout)

    def test_corrupt_git_index_fails_closed_instead_of_using_working_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            note = root / "notes.txt"
            note.write_text("sk" + "-" + "A" * 32 + "\n", encoding="utf-8")
            subprocess.run(["git", "add", "notes.txt"], cwd=root, check=True)
            note.write_text("benign working tree text\n", encoding="utf-8")
            (root / ".git" / "index").write_bytes(b"corrupt-index")

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("index", result.stdout.lower())
            self.assertIn("failed", result.stdout.lower())

    def test_git_detection_error_with_metadata_present_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            note = root / "notes.txt"
            note.write_text("sk" + "-" + "A" * 32 + "\n", encoding="utf-8")
            subprocess.run(["git", "add", "notes.txt"], cwd=root, check=True)
            note.write_text("benign working tree text\n", encoding="utf-8")
            (root / ".git" / "config").write_text("[malformed\n", encoding="utf-8")

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("Git repository detection failed", result.stdout)

    def test_missing_indexed_blob_returns_controlled_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            object_id = subprocess.run(
                ["git", "ls-files", "-s", "distribution.yaml"],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                check=True,
            ).stdout.split()[1]
            object_path = root / ".git" / "objects" / object_id[:2] / object_id[2:]
            object_path.unlink()

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("Git blob read failed", result.stdout)
            self.assertNotIn("Traceback", result.stdout)

    def test_untracked_files_are_scanned_directly_but_never_satisfy_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            cache = root / "scripts" / "__pycache__" / "package_contract.cpython-312.pyc"
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(b"interpreter cache")
            note = root / "notes.txt"
            note.write_text("benign untracked text\n", encoding="utf-8")

            benign = run_validate(root)
            self.assertEqual(benign.returncode, 0, benign.stdout)

            note.write_text("github" + "_pat_" + "A" * 40 + "\n", encoding="utf-8")
            secret = run_validate(root)
            self.assertNotEqual(secret.returncode, 0, secret.stdout)
            self.assertIn("GitHub", secret.stdout)
            self.assertNotIn("unreadable", secret.stdout.lower())


class PickHashBijectionTests(unittest.TestCase):
    def test_accepts_compact_alternative_value_role_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            card = root / "picks" / "full-card" / CARD_NAME
            content = "# Card\n\nPrimary win\nAlternative/value\nSafest show\n"
            card.write_text(content, encoding="utf-8")
            card.with_name(card.name + ".sha256").write_text(
                f"{hashlib.sha256(content.encode()).hexdigest()}  full-card/{CARD_NAME}\n",
                encoding="utf-8",
            )

            result = run_validate(root)

            self.assertEqual(result.returncode, 0, result.stdout)

    def test_rejects_a_full_card_without_its_same_basename_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            extra = root / "picks" / "full-card" / "2026-08-15-SAR-full-card.md"
            extra.write_text(CARD_CONTENT, encoding="utf-8")

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn(extra.name, result.stdout)
            self.assertIn("sidecar", result.stdout.lower())

    def test_rejects_an_orphan_decoy_sidecar_pointing_to_another_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            card = root / "picks" / "full-card" / CARD_NAME
            real_sidecar = card.with_name(card.name + ".sha256")
            decoy = card.with_name("decoy-full-card.md.sha256")
            real_sidecar.rename(decoy)

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn(card.name, result.stdout)
            self.assertIn(decoy.name, result.stdout)

    def test_rejects_sidecar_target_traversal_even_when_it_resolves_to_the_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            card = root / "picks" / "full-card" / CARD_NAME
            sidecar = card.with_name(card.name + ".sha256")
            sidecar.write_text(
                f"{hashlib.sha256(CARD_CONTENT.encode()).hexdigest()}  "
                f"full-card/../full-card/{CARD_NAME}\n",
                encoding="utf-8",
            )

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("must target", result.stdout.lower())


class DistributionYamlTests(unittest.TestCase):
    def test_accepts_equivalent_flow_style_yaml_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            values = MANIFEST_VALUES
            (root / "distribution.yaml").write_text(
                "{name: trotter, version: 0.1.0, "
                f"description: {values['description']!r}, "
                "hermes_requires: '>=0.20.0', "
                f"author: {values['author']!r}, license: MIT, "
                "distribution_owned: [SOUL.md, profile.yaml, skills/, distribution.yaml]}\n",
                encoding="utf-8",
            )

            result = run_validate(root)

            self.assertEqual(result.returncode, 0, result.stdout)

    def test_rejects_duplicate_yaml_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            manifest = manifest_yaml() + "name: malicious-shadow\n"
            (root / "distribution.yaml").write_text(manifest, encoding="utf-8")

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("duplicate", result.stdout.lower())

    def test_rejects_extra_distribution_owned_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            wrong = ["SOUL.md", "profile.yaml", "skills/", "distribution.yaml", "secrets/"]
            (root / "distribution.yaml").write_text(manifest_yaml(owned=wrong), encoding="utf-8")

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("distribution_owned", result.stdout)
            self.assertIn("exactly", result.stdout.lower())

    def test_rejects_reordered_distribution_owned_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            reordered = ["profile.yaml", "SOUL.md", "skills/", "distribution.yaml"]
            (root / "distribution.yaml").write_text(
                manifest_yaml(owned=reordered), encoding="utf-8"
            )

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("distribution_owned", result.stdout)
            self.assertIn("exactly", result.stdout.lower())

    def test_staged_manifest_deletion_is_not_replaced_by_untracked_working_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                ["git", "rm", "--cached", "distribution.yaml"],
                cwd=root,
                stdout=subprocess.DEVNULL,
                check=True,
            )

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("missing distribution.yaml", result.stdout)


class SkillLayoutTests(unittest.TestCase):
    def test_rejects_frontmatter_without_a_delimiter_only_closing_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            skill = root / "skills" / "horse-racing" / "trotter-handicapping" / "SKILL.md"
            skill.write_text(
                "---\nname: trotter-handicapping\ndescription: Test\n"
                "version: 1.0.0\n# --- appears only in a comment\nBody\n",
                encoding="utf-8",
            )

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("frontmatter", result.stdout.lower())

    def test_rejects_any_additional_skill_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            extra = root / "skills" / "other" / "trotter-handicapping" / "SKILL.md"
            extra.parent.mkdir(parents=True)
            extra.write_text(
                "---\nname: trotter-handicapping\ndescription: Extra\n"
                "version: 1.0.0\n---\n",
                encoding="utf-8",
            )

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("exactly one", result.stdout.lower())

    def test_rejects_wrong_canonical_skill_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            skill = root / "skills" / "horse-racing" / "trotter-handicapping" / "SKILL.md"
            skill.write_text(
                "---\nname: wrong-public-skill\ndescription: Test\nversion: 1.0.0\n---\n",
                encoding="utf-8",
            )

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("name", result.stdout.lower())
            self.assertIn("trotter-handicapping", result.stdout)

    def test_rejects_non_scalar_skill_identity_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            skill = root / "skills" / "horse-racing" / "trotter-handicapping" / "SKILL.md"
            skill.write_text(
                "---\nname: [trotter-handicapping]\ndescription: [Test]\n"
                "version: [1.0.0]\n---\n",
                encoding="utf-8",
            )

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("scalar", result.stdout.lower())


class PickIndexTests(unittest.TestCase):
    def test_rejects_a_stale_generated_picks_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            (root / "picks" / "README.md").write_text(
                "# Stale picks index\n", encoding="utf-8"
            )

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("picks/README.md", result.stdout)
            self.assertIn("stale", result.stdout.lower())

    def test_rejects_noncanonical_card_filename_metacharacters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            unsafe_name = "2026-08-15-SAR|INJECT-full-card.md"
            write_card(root, unsafe_name)

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn(unsafe_name, result.stdout)
            self.assertIn("filename", result.stdout.lower())

    def test_staged_card_deletion_is_not_replaced_by_working_copies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_validation_package(Path(tmp))
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            card = root / "picks" / "full-card" / CARD_NAME
            sidecar = card.with_name(card.name + ".sha256")
            subprocess.run(
                [
                    "git",
                    "rm",
                    "--cached",
                    card.relative_to(root).as_posix(),
                    sidecar.relative_to(root).as_posix(),
                ],
                cwd=root,
                stdout=subprocess.DEVNULL,
                check=True,
            )

            result = run_validate(root)

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("no full-card", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
