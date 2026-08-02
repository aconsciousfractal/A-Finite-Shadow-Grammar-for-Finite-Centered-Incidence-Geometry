#!/usr/bin/env python3
"""Bounded regression sentinels for the fail-closed public verifier."""

from __future__ import annotations

import argparse
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify = load_module(
    "p13_public_verify",
    PACKAGE_ROOT / "scripts" / "verify.py",
)
x15_adapter = load_module(
    "p13_x15_adapter",
    PACKAGE_ROOT / "scripts" / "signed_type_bc_shadow_replay.py",
)

TITLE_NAME = "A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry.pdf"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class VerifierFixture:
    def __init__(self) -> None:
        temp_root = os.environ.get("FCIG_TEST_TMPDIR") or os.environ.get("P13_TEST_TMPDIR")
        self.temp = tempfile.TemporaryDirectory(
            prefix="p13_s44h_verify_",
            dir=temp_root,
        )
        self.base = Path(self.temp.name)
        self.root = self.base / "package"
        self.marker = self.base / "route_invocations.txt"
        (self.root / "scripts").mkdir(parents=True)
        (self.root / "artifacts").mkdir()
        (self.root / "paper").mkdir()
        (self.root / ".gitignore").write_text(
            "artifacts/public_verify_result.json\nartifacts/.verify/\n",
            encoding="utf-8",
            newline="\n",
        )
        (self.root / "paper" / TITLE_NAME).write_bytes(
            b"bounded-pdf-fixture\n"
        )
        (self.root / "artifacts" / "frozen.json").write_text(
            json.dumps({"status": "PASS_FROZEN", "pass": True}) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (self.root / "scripts" / "mock_x15.py").write_text(
            "# mocked by test_verify_fail_closed.py\n",
            encoding="utf-8",
            newline="\n",
        )
        self.route = {
            "id": "X15",
            "status": "active",
            "kind": "bounded_replay",
            "script": "scripts/mock_x15.py",
            "args": ["--recompute"],
            "replay_artifact": "artifacts/.verify/x15.json",
            "artifacts": ["artifacts/frozen.json"],
        }
        self.write_registry(self.route)
        self.regenerate_checksums()

    def write_registry(self, route: dict[str, object]) -> None:
        payload = {
            "schema_version": verify.ROUTE_SCHEMA_VERSION,
            "policy": copy.deepcopy(verify.EXPECTED_ROUTE_POLICY),
            "routes": [route],
        }
        (self.root / "artifacts" / "public_evidence_routes.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def regenerate_checksums(self) -> None:
        manifest = self.root / "SHA256SUMS.txt"
        release = self.root / "RELEASE_SHA256.txt"
        ignored = {
            manifest,
            release,
            self.root / "artifacts" / "public_verify_result.json",
        }
        paths = []
        for path in self.root.rglob("*"):
            if not path.is_file() or path in ignored:
                continue
            if "artifacts/.verify" in path.as_posix():
                continue
            paths.append(path)
        manifest.write_text(
            "".join(
                f"{digest(path)}  {path.relative_to(self.root).as_posix()}\n"
                for path in sorted(paths)
            ),
            encoding="utf-8",
            newline="\n",
        )
        title = self.root / "paper" / TITLE_NAME
        release.write_text(
            f"{digest(manifest)}  SHA256SUMS.txt\n"
            f"{digest(title)}  paper/{TITLE_NAME}\n",
            encoding="utf-8",
            newline="\n",
        )

    def _subprocess_side_effect(
        self,
        mutate_frozen: bool,
        alias_output: bool,
    ):
        def invoke(command, *args, **kwargs):
            if (
                isinstance(command, list)
                and command
                and command[0] == "git"
            ):
                return verify.subprocess.CompletedProcess(
                    command,
                    1,
                    stdout=b"",
                    stderr=b"",
                )
            self.marker.parent.mkdir(parents=True, exist_ok=True)
            with self.marker.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write("invoked\n")
            out_index = command.index("--out") + 1
            runtime_output = Path(command[out_index])
            runtime_output.parent.mkdir(parents=True, exist_ok=True)
            runtime_output.write_text(
                json.dumps(
                    {
                        "status": "PASS_MOCK",
                        "pass": True,
                        "checks": {"mock": True},
                    }
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            if mutate_frozen:
                (self.root / "artifacts" / "frozen.json").write_text(
                    json.dumps({"status": "MUTATED", "pass": False}) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
            if alias_output:
                envelope_output = (
                    self.root
                    / "artifacts"
                    / "public_verify_result.json"
                )
                envelope_output.unlink(missing_ok=True)
                os.link(
                    self.root / "artifacts" / "frozen.json",
                    envelope_output,
                )
            return verify.subprocess.CompletedProcess(
                command,
                0,
                stdout='{"pass": true}',
                stderr="",
            )

        return invoke

    def patches(
        self,
        output: Path,
        *,
        static_only: bool = False,
        mutate_frozen: bool = False,
        alias_output: bool = False,
    ) -> ExitStack:
        stack = ExitStack()
        values = {
            "ROOT": self.root,
            "ROUTES_PATH": (
                self.root / "artifacts" / "public_evidence_routes.json"
            ),
            "MANIFEST_PATH": self.root / "SHA256SUMS.txt",
            "RELEASE_PATH": self.root / "RELEASE_SHA256.txt",
            "TITLE_PDF_PATH": self.root / "paper" / TITLE_NAME,
            "DEFAULT_OUT": output,
            "CHECKSUM_METADATA": {
                "SHA256SUMS.txt",
                "RELEASE_SHA256.txt",
            },
            "RELEASE_REQUIRED_PATHS": {
                "SHA256SUMS.txt",
                f"paper/{TITLE_NAME}",
            },
            "REQUIRED_ROUTE_IDS": ("X15",),
            "EXPECTED_ROUTE_SCRIPTS": {"X15": "scripts/mock_x15.py"},
            "EXPECTED_ROUTE_ARTIFACTS": {
                "X15": ("artifacts/frozen.json",)
            },
            "EXPECTED_ROUTE_ARGS": {"X15": ("--recompute",)},
            "EXPECTED_OPTIONAL_SCRIPTS": {},
            "X15_REPLAY_ARTIFACT": "artifacts/.verify/x15.json",
        }
        stack.enter_context(mock.patch.multiple(verify, **values))
        stack.enter_context(
            mock.patch.object(
                verify,
                "parse_args",
                return_value=argparse.Namespace(
                    static_only=static_only,
                    timeout=30,
                    output=output,
                ),
            )
        )
        stack.enter_context(
            mock.patch.object(
                verify.subprocess,
                "run",
                side_effect=self._subprocess_side_effect(
                    mutate_frozen,
                    alias_output,
                ),
            )
        )
        return stack

    def close(self) -> None:
        self.temp.cleanup()


class FailClosedVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = VerifierFixture()
        self.output = (
            self.fixture.root / "artifacts" / "public_verify_result.json"
        )

    def tearDown(self) -> None:
        self.fixture.close()

    def run_main(
        self,
        *,
        static_only: bool = False,
        mutate_frozen: bool = False,
        alias_output: bool = False,
    ) -> tuple[int, dict[str, object]]:
        with (
            self.fixture.patches(
                self.output,
                static_only=static_only,
                mutate_frozen=mutate_frozen,
                alias_output=alias_output,
            ),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            code = verify.main()
        envelope = json.loads(self.output.read_text(encoding="utf-8"))
        return code, envelope

    def test_bad_manifest_invokes_zero_routes(self) -> None:
        manifest = self.fixture.root / "SHA256SUMS.txt"
        text = manifest.read_text(encoding="utf-8")
        manifest.write_text("0" + text[1:], encoding="utf-8", newline="\n")
        code, envelope = self.run_main()
        self.assertEqual(code, 1)
        self.assertEqual(envelope["counts"]["routes_invoked"], 0)
        self.assertFalse(self.fixture.marker.exists())

    def test_missing_outer_invokes_zero_routes(self) -> None:
        (self.fixture.root / "RELEASE_SHA256.txt").unlink()
        code, envelope = self.run_main()
        self.assertEqual(code, 1)
        self.assertEqual(envelope["counts"]["routes_invoked"], 0)
        self.assertFalse(self.fixture.marker.exists())

    def test_escaping_route_invokes_zero_routes(self) -> None:
        route = copy.deepcopy(self.fixture.route)
        route["script"] = "../../outside.py"
        self.fixture.write_registry(route)
        self.fixture.regenerate_checksums()
        code, envelope = self.run_main()
        self.assertEqual(code, 1)
        self.assertEqual(envelope["counts"]["routes_invoked"], 0)
        self.assertFalse(envelope["checks"]["route_schema_pass"])
        self.assertFalse(self.fixture.marker.exists())

    def test_unbounded_args_invoke_zero_routes(self) -> None:
        route = copy.deepcopy(self.fixture.route)
        route["args"] = ["--recompute", "../../outside.py"]
        self.fixture.write_registry(route)
        self.fixture.regenerate_checksums()
        code, envelope = self.run_main()
        self.assertEqual(code, 1)
        self.assertEqual(envelope["counts"]["routes_invoked"], 0)
        self.assertFalse(envelope["checks"]["route_schema_pass"])
        self.assertFalse(self.fixture.marker.exists())

    def test_policy_contract_is_required(self) -> None:
        registry = self.fixture.root / "artifacts" / "public_evidence_routes.json"
        payload = json.loads(registry.read_text(encoding="utf-8"))
        payload["policy"].pop("release_checksum_checked_before_execution")
        registry.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        self.fixture.regenerate_checksums()
        code, envelope = self.run_main()
        self.assertEqual(code, 1)
        self.assertEqual(envelope["counts"]["routes_invoked"], 0)
        self.assertEqual(
            envelope["route_error"],
            "route_document_contract_invalid",
        )
        self.assertFalse(self.fixture.marker.exists())

    def test_run_twice_preserves_integrity_layers_and_frozen_artifact(self) -> None:
        manifest = self.fixture.root / "SHA256SUMS.txt"
        release = self.fixture.root / "RELEASE_SHA256.txt"
        frozen = self.fixture.root / "artifacts" / "frozen.json"
        before = (digest(manifest), digest(release), digest(frozen))

        first_code, first = self.run_main()
        second_code, second = self.run_main()

        self.assertEqual((first_code, second_code), (0, 0))
        self.assertTrue(first["pass"])
        self.assertTrue(second["pass"])
        self.assertEqual(first["counts"]["routes_invoked"], 1)
        self.assertEqual(second["counts"]["routes_invoked"], 1)
        self.assertEqual(
            before,
            (digest(manifest), digest(release), digest(frozen)),
        )
        self.assertEqual(
            self.fixture.marker.read_text(encoding="utf-8").splitlines(),
            ["invoked", "invoked"],
        )
        self.assertFalse((self.fixture.root / "artifacts" / ".verify").exists())

    def test_static_mode_counts_zero_subprocesses(self) -> None:
        code, envelope = self.run_main(static_only=True)
        self.assertEqual(code, 0)
        self.assertTrue(envelope["pass"])
        self.assertEqual(envelope["counts"]["routes_evaluated"], 1)
        self.assertEqual(envelope["counts"]["routes_invoked"], 0)
        self.assertFalse(self.fixture.marker.exists())

    def test_git_unsafe_discovery_fails_closed(self) -> None:
        unsafe = verify.subprocess.CompletedProcess(
            ["git"],
            0,
            stdout=b"../outside.py\0",
            stderr=b"",
        )
        with (
            self.fixture.patches(self.output),
            mock.patch.object(
                verify.subprocess,
                "run",
                return_value=unsafe,
            ),
        ):
            files, method, error = verify.distributed_files()
        self.assertEqual(files, set())
        self.assertEqual(method, "git_ls_files")
        self.assertIn("unsafe_distributed_path", error or "")

    def test_git_missing_entry_fails_closed(self) -> None:
        missing = verify.subprocess.CompletedProcess(
            ["git"],
            0,
            stdout=b"artifacts/public_verify_result.json\0",
            stderr=b"",
        )
        with (
            self.fixture.patches(self.output),
            mock.patch.object(
                verify.subprocess,
                "run",
                return_value=missing,
            ),
        ):
            files, method, error = verify.distributed_files()
        self.assertEqual(files, set())
        self.assertEqual(method, "git_ls_files")
        self.assertIn(
            "tracked_or_untracked_entry_missing",
            error or "",
        )

    def test_runtime_parent_alias_invokes_zero_subprocesses(self) -> None:
        runtime_parent = self.fixture.root / "artifacts" / ".verify"
        real_resolve = Path.resolve

        def spoof_resolve(path, *args, **kwargs):
            if path == runtime_parent:
                return self.fixture.root / "artifacts"
            return real_resolve(path, *args, **kwargs)

        with (
            self.fixture.patches(self.output),
            mock.patch.object(Path, "resolve", spoof_resolve),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            code = verify.main()
        envelope = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(code, 1)
        self.assertEqual(envelope["counts"]["routes_invoked"], 0)
        self.assertFalse(
            envelope["routes"][0]["checks"]["runtime_artifact_prepared"]
        )
        self.assertFalse(runtime_parent.exists())

    def test_output_hardlink_is_broken_before_preflight(self) -> None:
        manifest = self.fixture.root / "SHA256SUMS.txt"
        before = digest(manifest)
        try:
            os.link(manifest, self.output)
        except OSError as exc:
            self.skipTest(f"hardlinks unavailable: {exc}")
        self.assertTrue(self.output.samefile(manifest))

        code, envelope = self.run_main()

        self.assertEqual(code, 0)
        self.assertTrue(envelope["pass"])
        self.assertEqual(digest(manifest), before)
        self.assertFalse(self.output.samefile(manifest))

    def test_route_created_output_alias_is_broken_after_postflight(
        self,
    ) -> None:
        frozen = self.fixture.root / "artifacts" / "frozen.json"
        probe = self.fixture.base / "hardlink_probe"
        try:
            os.link(frozen, probe)
        except OSError as exc:
            self.skipTest(f"hardlinks unavailable: {exc}")
        finally:
            probe.unlink(missing_ok=True)
        before = digest(frozen)

        code, envelope = self.run_main(alias_output=True)

        self.assertEqual(code, 0)
        self.assertTrue(envelope["pass"])
        self.assertEqual(digest(frozen), before)
        self.assertFalse(self.output.samefile(frozen))

    def test_route_mutation_fails_route_and_postflight(self) -> None:
        code, envelope = self.run_main(mutate_frozen=True)
        self.assertEqual(code, 1)
        self.assertFalse(envelope["pass"])
        self.assertEqual(envelope["counts"]["routes_invoked"], 1)
        self.assertFalse(
            envelope["routes"][0]["checks"][
                "distributed_artifacts_immutable"
            ]
        )
        self.assertFalse(
            envelope["checks"]["manifest_postflight_pass"]
        )

    def test_real_registry_contract(self) -> None:
        document = json.loads(
            (
                PACKAGE_ROOT
                / "artifacts"
                / "public_evidence_routes.json"
            ).read_text(encoding="utf-8")
        )
        ok, coverage, routes, details, error = (
            verify.validate_route_document(document)
        )
        self.assertTrue(ok)
        self.assertTrue(coverage)
        self.assertIsNone(error)
        self.assertEqual(len(routes), 12)
        self.assertTrue(all(item["pass"] for item in details))

    def test_x15_recompute_rejects_distributed_outputs_before_loading(self) -> None:
        manifest = PACKAGE_ROOT / "SHA256SUMS.txt"
        before = digest(manifest)
        with (
            mock.patch.object(
                x15_adapter,
                "parse_args",
                return_value=argparse.Namespace(
                    recompute=True,
                    output=manifest,
                ),
            ),
            mock.patch.object(
                x15_adapter,
                "load_payload",
                side_effect=AssertionError("must not load"),
            ),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            code = x15_adapter.main()
        self.assertEqual(code, 2)
        self.assertEqual(digest(manifest), before)

        default_target, default_error = x15_adapter.validate_output(
            x15_adapter.DEFAULT_OUT,
            True,
        )
        other_target, other_error = x15_adapter.validate_output(
            manifest,
            True,
        )
        safe_target, safe_error = x15_adapter.validate_output(
            x15_adapter.VERIFY_OUTPUT_DIR / "sentinel.json",
            True,
        )
        self.assertIsNone(default_target)
        self.assertIsNotNone(default_error)
        self.assertIsNone(other_target)
        self.assertIsNotNone(other_error)
        self.assertIsNotNone(safe_target)
        self.assertIsNone(safe_error)


if __name__ == "__main__":
    unittest.main()
