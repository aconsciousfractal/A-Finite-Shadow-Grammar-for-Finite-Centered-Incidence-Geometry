#!/usr/bin/env python3
"""Fail-closed public verifier for the finite-shadow grammar package."""

from __future__ import annotations

import argparse
from fnmatch import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "artifacts" / "public_evidence_routes.json"
MANIFEST_PATH = ROOT / "SHA256SUMS.txt"
RELEASE_PATH = ROOT / "RELEASE_SHA256.txt"
TITLE_PDF_PATH = (
    ROOT
    / "paper"
    / "A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry.pdf"
)
DEFAULT_OUT = ROOT / "artifacts" / "public_verify_result.json"

CHECKSUM_METADATA = {MANIFEST_PATH.name, RELEASE_PATH.name}
RELEASE_REQUIRED_PATHS = {
    MANIFEST_PATH.name,
    TITLE_PDF_PATH.relative_to(ROOT).as_posix(),
}
REQUIRED_ROUTE_IDS = (
    "X05",
    "X15",
    "X16",
    "X18",
    "X19",
    "X20",
    "X21",
    "X22",
    "X23",
    "X24",
    "X25",
    "X26",
)
EXPECTED_ROUTE_SCRIPTS = {
    "X05": "scripts/x05_m19_lat565_evidence_check.py",
    "X15": "scripts/signed_type_bc_shadow_replay.py",
    "X16": "scripts/modular_centered_channel_replay.py",
    "X18": "scripts/dihedral_vertex_shadow_replay.py",
    "X19": "scripts/g2_source_channel_replay.py",
    "X20": "scripts/f4_source_layer_replay.py",
    "X21": "scripts/h3_projective_source_channel_replay.py",
    "X22": "scripts/h4_projective_source_channel_replay.py",
    "X23": "scripts/d5_projective_source_channel_replay.py",
    "X24": "scripts/e6_projective_source_channel_replay.py",
    "X25": "scripts/e7_projective_source_channel_replay.py",
    "X26": "scripts/e8_projective_source_channel_replay.py",
}
EXPECTED_ROUTE_ARTIFACTS = {
    "X05": ("artifacts/x05_m19_lat565_evidence_check.json",),
    "X15": ("artifacts/signed_type_bc_shadow_replay.json",),
    "X16": ("artifacts/modular_centered_channel_replay.json",),
    "X18": ("artifacts/dihedral_vertex_shadow_replay.json",),
    "X19": ("artifacts/g2_source_channel_replay.json",),
    "X20": ("artifacts/f4_source_layer_replay.json",),
    "X21": ("artifacts/h3_projective_source_channel_replay.json",),
    "X22": ("artifacts/h4_projective_source_channel_replay.json",),
    "X23": ("artifacts/d5_projective_source_channel_replay.json",),
    "X24": ("artifacts/e6_projective_source_channel_replay.json",),
    "X25": ("artifacts/e7_projective_source_channel_replay.json",),
    "X26": ("artifacts/e8_projective_source_channel_replay.json",),
}
EXPECTED_ROUTE_ARGS = {route_id: () for route_id in REQUIRED_ROUTE_IDS}
EXPECTED_ROUTE_ARGS["X15"] = ("--recompute",)
EXPECTED_OPTIONAL_SCRIPTS = {
    "X05": "scripts/x05_m19_census_full_regeneration.py",
}
X15_REPLAY_ARTIFACT = "artifacts/.verify/signed_type_bc_shadow_recompute.json"
ROUTE_SCHEMA_VERSION = 3
EXPECTED_ROUTE_POLICY = {
    "all_quantitative_routes_required": True,
    "full_x05_census_is_optional": True,
    "manifest_checked_before_execution": True,
    "release_checksum_checked_before_execution": True,
    "semantic_artifact_check_required": True,
    "distributed_artifacts_immutable": True,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def canonical_package_path(value: Any) -> tuple[Path | None, str | None]:
    """Resolve one canonical POSIX package-relative path inside ROOT."""

    if not isinstance(value, str) or not value or value.strip() != value:
        return None, "missing_or_whitespace_path"
    if "\\" in value or ":" in value or any(ord(char) < 32 for char in value):
        return None, "backslash_drive_or_control_character"
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != value:
        return None, "absolute_parent_or_noncanonical_path"
    target = ROOT.joinpath(*pure.parts)
    try:
        resolved = target.resolve()
        root_resolved = ROOT.resolve()
    except (OSError, RuntimeError, UnicodeError) as exc:
        return None, f"resolve_failed:{type(exc).__name__}"
    if not resolved.is_relative_to(root_resolved):
        return None, "path_outside_root"
    return target, None


def _gitignore_patterns() -> list[str]:
    path = ROOT / ".gitignore"
    if not path.is_file():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def _pattern_matches(rel: str, raw_pattern: str) -> bool:
    pattern = raw_pattern[1:] if raw_pattern.startswith("!") else raw_pattern
    anchored = pattern.startswith("/")
    if anchored:
        pattern = pattern[1:]
    directory_only = pattern.endswith("/")
    if directory_only:
        pattern = pattern[:-1]
    if not pattern:
        return False

    parts = rel.split("/")
    if directory_only:
        prefixes = ["/".join(parts[:index]) for index in range(1, len(parts))]
        if "/" not in pattern:
            return any(fnmatch(part, pattern) for part in parts[:-1])
        if anchored:
            return any(fnmatch(prefix, pattern) for prefix in prefixes)
        return any(
            fnmatch(prefix, pattern) or fnmatch(prefix, f"*/{pattern}")
            for prefix in prefixes
        )
    if "/" not in pattern:
        return fnmatch(parts[-1], pattern)
    if anchored:
        return fnmatch(rel, pattern)
    return fnmatch(rel, pattern) or fnmatch(rel, f"*/{pattern}")


def _ignored_by_fallback(rel: str, patterns: list[str]) -> bool:
    ignored = False
    for raw in patterns:
        if not raw or raw.startswith("#"):
            continue
        if _pattern_matches(rel, raw):
            ignored = not raw.startswith("!")
    return ignored


def distributed_files() -> tuple[set[str], str, str | None]:
    try:
        root_resolved = ROOT.resolve()
    except (OSError, RuntimeError, UnicodeError) as exc:
        return set(), "unavailable", f"{type(exc).__name__}: {exc}"
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
            ],
            capture_output=True,
            check=False,
        )
    except (OSError, RuntimeError):
        completed = None

    if completed is not None and completed.returncode == 0:
        paths: set[str] = set()
        try:
            decoded = completed.stdout.decode(
                "utf-8", errors="surrogateescape"
            )
        except UnicodeError as exc:
            return (
                set(),
                "git_ls_files",
                f"git_output_decode_failed:{type(exc).__name__}",
            )
        for item in decoded.split("\0"):
            rel = item.replace("\\", "/")
            if (
                not rel
                or rel in CHECKSUM_METADATA
                or rel.startswith(".git/")
            ):
                continue
            target, error = canonical_package_path(rel)
            if error is not None or target is None:
                return (
                    set(),
                    "git_ls_files",
                    f"unsafe_distributed_path:{rel}:{error or 'invalid'}",
                )
            try:
                if target.is_symlink():
                    return (
                        set(),
                        "git_ls_files",
                        f"unsafe_distributed_path:{rel}:symlink",
                    )
                if target.is_file():
                    paths.add(rel)
                elif target.exists():
                    return (
                        set(),
                        "git_ls_files",
                        f"unsafe_distributed_path:{rel}:not_regular_file",
                    )
                else:
                    return (
                        set(),
                        "git_ls_files",
                        (
                            "tracked_or_untracked_entry_missing:"
                            f"{rel}"
                        ),
                    )
            except (OSError, RuntimeError, UnicodeError) as exc:
                return (
                    set(),
                    "git_ls_files",
                    f"unsafe_distributed_path:{rel}:{type(exc).__name__}",
                )
        return paths, "git_ls_files", None

    try:
        patterns = _gitignore_patterns()
        paths = set()
        for target in ROOT.rglob("*"):
            rel = target.relative_to(ROOT).as_posix()
            if rel in CHECKSUM_METADATA or rel.startswith(".git/"):
                continue
            if _ignored_by_fallback(rel, patterns):
                continue
            if target.is_symlink():
                return (
                    set(),
                    "filesystem_gitignore_fallback",
                    f"unsafe_distributed_path:{rel}:symlink",
                )
            if not target.is_file():
                continue
            resolved = target.resolve()
            if not resolved.is_relative_to(root_resolved):
                return (
                    set(),
                    "filesystem_gitignore_fallback",
                    f"unsafe_distributed_path:{rel}:path_outside_root",
                )
            paths.add(rel)
        return paths, "filesystem_gitignore_fallback", None
    except (OSError, RuntimeError, UnicodeError) as exc:
        return set(), "unavailable", f"{type(exc).__name__}: {exc}"

def _empty_manifest_detail(reason: str) -> dict[str, Any]:
    return {
        "checks": {
            "manifest_present": False,
            "entries_present": False,
            "entry_hashes_pass": False,
            "entries_unique": False,
            "discovery_succeeded": False,
            "coverage_complete": False,
            "no_extra_entries": False,
        },
        "discovery_method": "not_run",
        "discovery_error": reason,
        "distributed_files": 0,
        "declared_entries": 0,
        "missing_from_manifest": [],
        "extra_manifest_entries": [],
    }


def verify_manifest(
    path: Path,
) -> tuple[bool, list[dict[str, Any]], dict[str, Any]]:
    results: list[dict[str, Any]] = []
    declared_paths: list[str] = []
    seen: set[str] = set()
    if not path.is_file():
        detail = _empty_manifest_detail("missing_manifest")
        return (
            False,
            [{"path": str(path), "ok": False, "reason": "missing_manifest"}],
            detail,
        )
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        detail = _empty_manifest_detail(type(exc).__name__)
        return (
            False,
            [{"path": str(path), "ok": False, "reason": type(exc).__name__}],
            detail,
        )

    for line_number, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        parts = raw.split(None, 1)
        if len(parts) != 2:
            results.append(
                {"line": line_number, "ok": False, "reason": "malformed"}
            )
            continue
        expected, rel = parts[0], parts[1].strip()
        target, path_error = canonical_package_path(rel)
        hash_ok = re.fullmatch(r"[0-9A-Fa-f]{64}", expected) is not None
        if path_error is not None or target is None:
            results.append(
                {
                    "line": line_number,
                    "path": rel,
                    "ok": False,
                    "reason": path_error or "invalid_path",
                }
            )
            continue

        duplicate = rel in seen
        seen.add(rel)
        declared_paths.append(rel)
        if rel in CHECKSUM_METADATA:
            results.append(
                {
                    "line": line_number,
                    "path": rel,
                    "ok": False,
                    "reason": "checksum_metadata_must_not_self_pin",
                }
            )
            continue
        if not target.is_file():
            results.append(
                {
                    "line": line_number,
                    "path": rel,
                    "ok": False,
                    "reason": "missing",
                    "duplicate": duplicate,
                    "hash_format_ok": hash_ok,
                }
            )
            continue

        actual = sha256(target)
        ok = hash_ok and not duplicate and actual == expected.upper()
        results.append(
            {
                "line": line_number,
                "path": rel,
                "expected": expected.upper(),
                "actual": actual,
                "duplicate": duplicate,
                "hash_format_ok": hash_ok,
                "ok": ok,
            }
        )

    distributed, method, discovery_error = distributed_files()
    declared_unique = set(declared_paths)
    missing = sorted(distributed - declared_unique)
    extra = sorted(declared_unique - distributed)
    checks = {
        "manifest_present": True,
        "entries_present": bool(results),
        "entry_hashes_pass": bool(results)
        and all(item["ok"] for item in results),
        "entries_unique": len(declared_paths) == len(declared_unique),
        "discovery_succeeded": discovery_error is None,
        "coverage_complete": not missing,
        "no_extra_entries": not extra,
    }
    detail = {
        "checks": checks,
        "discovery_method": method,
        "discovery_error": discovery_error,
        "distributed_files": len(distributed),
        "declared_entries": len(declared_paths),
        "missing_from_manifest": missing,
        "extra_manifest_entries": extra,
    }
    return all(checks.values()), results, detail


def verify_release_checksum(
    path: Path,
) -> tuple[bool, list[dict[str, Any]], dict[str, Any]]:
    results: list[dict[str, Any]] = []
    declared: list[str] = []
    seen: set[str] = set()
    base_checks = {
        "release_checksum_present": path.is_file(),
        "entries_exact": False,
        "entries_unique": False,
        "entry_hashes_pass": False,
    }
    if not path.is_file():
        detail = {
            "checks": base_checks,
            "required_paths": sorted(RELEASE_REQUIRED_PATHS),
            "declared_paths": [],
        }
        return (
            False,
            [
                {
                    "path": str(path),
                    "ok": False,
                    "reason": "missing_release_checksum",
                }
            ],
            detail,
        )
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        detail = {
            "checks": base_checks,
            "required_paths": sorted(RELEASE_REQUIRED_PATHS),
            "declared_paths": [],
        }
        return (
            False,
            [{"path": str(path), "ok": False, "reason": type(exc).__name__}],
            detail,
        )

    for line_number, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        parts = raw.split(None, 1)
        if len(parts) != 2:
            results.append(
                {"line": line_number, "ok": False, "reason": "malformed"}
            )
            continue
        expected, rel = parts[0], parts[1].strip()
        target, path_error = canonical_package_path(rel)
        hash_ok = re.fullmatch(r"[0-9A-Fa-f]{64}", expected) is not None
        if path_error is not None or target is None:
            results.append(
                {
                    "line": line_number,
                    "path": rel,
                    "ok": False,
                    "reason": path_error or "invalid_path",
                }
            )
            continue
        duplicate = rel in seen
        seen.add(rel)
        declared.append(rel)
        if not target.is_file():
            results.append(
                {
                    "line": line_number,
                    "path": rel,
                    "ok": False,
                    "reason": "missing",
                    "duplicate": duplicate,
                    "hash_format_ok": hash_ok,
                }
            )
            continue
        actual = sha256(target)
        ok = hash_ok and not duplicate and actual == expected.upper()
        results.append(
            {
                "line": line_number,
                "path": rel,
                "expected": expected.upper(),
                "actual": actual,
                "duplicate": duplicate,
                "hash_format_ok": hash_ok,
                "ok": ok,
            }
        )

    declared_set = set(declared)
    checks = {
        "release_checksum_present": True,
        "entries_exact": declared_set == RELEASE_REQUIRED_PATHS,
        "entries_unique": len(declared) == len(declared_set),
        "entry_hashes_pass": bool(results)
        and all(item["ok"] for item in results),
    }
    detail = {
        "checks": checks,
        "required_paths": sorted(RELEASE_REQUIRED_PATHS),
        "declared_paths": declared,
    }
    return all(checks.values()), results, detail


def artifact_truth(data: Any) -> tuple[bool, dict[str, Any]]:
    if not isinstance(data, dict):
        return False, {"reason": "artifact_not_object"}

    markers: list[bool] = []
    for key in ("pass", "all_pass"):
        if key in data:
            markers.append(data[key] is True)
    status = data.get("status")
    if isinstance(status, str):
        markers.append(status.upper().startswith("PASS"))
    summary = data.get("summary")
    if isinstance(summary, dict):
        if "pass" in summary:
            markers.append(summary["pass"] is True)
        summary_status = summary.get("status")
        if isinstance(summary_status, str):
            markers.append(summary_status.upper().startswith("PASS"))
    checks = data.get("checks")
    false_checks = []
    if isinstance(checks, dict):
        false_checks = [
            str(key) for key, value in checks.items() if value is not True
        ]
    if not markers:
        return (
            False,
            {"reason": "no_explicit_pass_marker", "false_checks": false_checks},
        )
    ok = all(markers) and not false_checks
    return (
        ok,
        {
            "markers": markers,
            "false_checks": false_checks,
            "reason": "ok" if ok else "failed_marker_or_check",
        },
    )


def load_routes() -> dict[str, Any]:
    return json.loads(ROUTES_PATH.read_text(encoding="utf-8"))


def _path_list(
    route: dict[str, Any],
    field: str,
    required: bool,
) -> tuple[bool, list[str], list[str]]:
    value = route.get(field)
    if value is None and not required:
        return True, [], []
    if not isinstance(value, list) or (required and not value):
        return False, [], [f"{field}:not_a_nonempty_list"]
    valid: list[str] = []
    errors: list[str] = []
    for index, item in enumerate(value):
        target, error = canonical_package_path(item)
        if target is None or error is not None:
            errors.append(f"{field}[{index}]:{error or 'invalid'}")
        else:
            valid.append(item)
    if len(valid) != len(set(valid)):
        errors.append(f"{field}:duplicate_path")
    return not errors, valid, errors


def validate_route(route: Any) -> tuple[bool, dict[str, Any]]:
    if not isinstance(route, dict):
        return (
            False,
            {
                "id": None,
                "checks": {"route_is_object": False},
                "errors": ["route_not_object"],
                "pass": False,
            },
        )

    row_id = route.get("id")
    checks: dict[str, bool] = {
        "route_is_object": True,
        "id_known": isinstance(row_id, str)
        and row_id in REQUIRED_ROUTE_IDS,
        "status_active": route.get("status") == "active",
        "kind_declared": isinstance(route.get("kind"), str)
        and bool(route.get("kind")),
    }
    errors: list[str] = []

    script = route.get("script")
    script_target, script_error = canonical_package_path(script)
    checks["script_path_canonical"] = (
        script_error is None and script_target is not None
    )
    checks["script_contract_exact"] = (
        checks["id_known"]
        and script == EXPECTED_ROUTE_SCRIPTS.get(row_id)
    )
    if script_error is not None:
        errors.append(f"script:{script_error}")

    required_ok, _, required_errors = _path_list(
        route, "required_files", required=False
    )
    artifacts_ok, artifacts, artifact_errors = _path_list(
        route, "artifacts", required=True
    )
    checks["required_file_paths_canonical"] = required_ok
    checks["artifact_paths_canonical"] = artifacts_ok
    checks["artifact_contract_exact"] = (
        checks["id_known"]
        and tuple(artifacts) == EXPECTED_ROUTE_ARTIFACTS.get(row_id)
    )
    errors.extend(required_errors)
    errors.extend(artifact_errors)

    args = route.get("args", [])
    checks["args_are_strings"] = isinstance(args, list) and all(
        isinstance(item, str) for item in args
    )
    checks["args_contract_exact"] = (
        checks["id_known"]
        and checks["args_are_strings"]
        and tuple(args) == EXPECTED_ROUTE_ARGS.get(row_id)
    )

    optional_script = route.get("optional_script")
    expected_optional = EXPECTED_OPTIONAL_SCRIPTS.get(row_id)
    if optional_script is None:
        checks["optional_script_contract"] = expected_optional is None
    else:
        optional_target, optional_error = canonical_package_path(
            optional_script
        )
        checks["optional_script_contract"] = (
            optional_error is None
            and optional_target is not None
            and optional_script == expected_optional
        )
        if optional_error is not None:
            errors.append(f"optional_script:{optional_error}")

    replay_artifact = route.get("replay_artifact")
    if replay_artifact is None:
        checks["replay_artifact_contract"] = row_id != "X15"
    else:
        replay_target, replay_error = canonical_package_path(
            replay_artifact
        )
        checks["replay_artifact_contract"] = (
            row_id == "X15"
            and replay_error is None
            and replay_target is not None
            and replay_artifact == X15_REPLAY_ARTIFACT
            and replay_artifact.startswith("artifacts/.verify/")
        )
        if replay_error is not None:
            errors.append(f"replay_artifact:{replay_error}")

    passed = all(checks.values()) and not errors
    return (
        passed,
        {
            "id": row_id,
            "checks": checks,
            "errors": errors,
            "pass": passed,
        },
    )


def validate_route_document(
    document: Any,
) -> tuple[
    bool,
    bool,
    list[dict[str, Any]],
    list[dict[str, Any]],
    str | None,
]:
    if not isinstance(document, dict):
        return False, False, [], [], "route_document_not_object"
    document_contract_ok = (
        document.get("schema_version") == ROUTE_SCHEMA_VERSION
        and document.get("policy") == EXPECTED_ROUTE_POLICY
    )
    raw_routes = document.get("routes")
    if not isinstance(raw_routes, list) or not raw_routes:
        return False, False, [], [], "routes_not_nonempty_list"

    validations = [validate_route(route) for route in raw_routes]
    details = [detail for _, detail in validations]
    routes = [route for route in raw_routes if isinstance(route, dict)]
    ids = [route.get("id") for route in routes]
    coverage_ok = (
        len(routes) == len(raw_routes) == len(REQUIRED_ROUTE_IDS)
        and len(ids) == len(set(ids))
        and set(ids) == set(REQUIRED_ROUTE_IDS)
    )
    schema_ok = (
        document_contract_ok and all(ok for ok, _ in validations)
    )
    route_error = (
        None if document_contract_ok else "route_document_contract_invalid"
    )
    return schema_ok, coverage_ok, routes, details, route_error

def _artifact_result(rel: str) -> dict[str, Any]:
    path, path_error = canonical_package_path(rel)
    if path is None or path_error is not None:
        return {
            "path": rel,
            "ok": False,
            "reason": path_error or "invalid_path",
        }
    if not path.is_file():
        return {"path": rel, "ok": False, "reason": "missing"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {
            "path": rel,
            "ok": False,
            "reason": type(exc).__name__,
        }
    ok, detail = artifact_truth(data)
    return {"path": rel, "ok": ok, "detail": detail}


def _hash_artifacts(paths: list[str]) -> dict[str, str]:
    hashes = {}
    for rel in paths:
        target, error = canonical_package_path(rel)
        if error is None and target is not None and target.is_file():
            hashes[rel] = sha256(target)
    return hashes


def run_route(
    route: dict[str, Any],
    static_only: bool,
    timeout: int,
) -> dict[str, Any]:
    contract_ok, contract = validate_route(route)
    row_id = route.get("id", "UNKNOWN")
    result: dict[str, Any] = {
        "id": row_id,
        "declared_status": route.get("status"),
        "kind": route.get("kind"),
        "checks": {"route_contract_valid": contract_ok},
        "route_contract": contract,
        "subprocess_invoked": False,
    }
    if not contract_ok:
        result["pass"] = False
        return result

    ready = route.get("status") == "active"
    result["checks"]["route_active"] = ready
    script = route["script"]
    script_target, _ = canonical_package_path(script)
    result["checks"]["script_declared"] = script_target is not None

    required_inputs = [script, *route.get("required_files", [])]
    missing = []
    for rel in required_inputs:
        target, _ = canonical_package_path(rel)
        if target is None or not target.is_file():
            missing.append(rel)
    result["required_inputs"] = required_inputs
    result["missing_required_files"] = missing
    result["missing_files"] = missing
    result["checks"]["required_files_present"] = not missing

    distributed_artifacts = list(route["artifacts"])
    result["declared_artifacts"] = distributed_artifacts
    before_hashes = _hash_artifacts(distributed_artifacts)

    replay_rel = route.get("replay_artifact") if not static_only else None
    replay_target: Path | None = None
    if replay_rel is not None:
        replay_target, _ = canonical_package_path(replay_rel)
        if replay_target is not None:
            try:
                expected_runtime_parent = (
                    ROOT.resolve() / "artifacts" / ".verify"
                )
                parent_before = replay_target.parent.resolve()
                if (
                    replay_target.parent.is_symlink()
                    or parent_before != expected_runtime_parent
                ):
                    raise RuntimeError("unsafe_runtime_artifact_parent")
                replay_target.parent.mkdir(parents=True, exist_ok=True)
                parent_after = replay_target.parent.resolve()
                if (
                    replay_target.parent.is_symlink()
                    or parent_after != expected_runtime_parent
                    or replay_target.is_dir()
                ):
                    raise RuntimeError("unsafe_runtime_artifact_target")
                replay_target.unlink(missing_ok=True)
            except (OSError, RuntimeError, UnicodeError) as exc:
                result["checks"]["runtime_artifact_prepared"] = False
                result["runtime_artifact_error"] = (
                    f"{type(exc).__name__}: {exc}"
                )
            else:
                result["checks"]["runtime_artifact_prepared"] = True

    can_execute = (
        not static_only
        and ready
        and script_target is not None
        and not missing
        and (
            replay_rel is None
            or result["checks"].get("runtime_artifact_prepared") is True
        )
    )
    if can_execute:
        command = [sys.executable, "-B", str(script_target)]
        command.extend(route.get("args", []))
        if replay_target is not None:
            command.extend(["--out", str(replay_target)])
        try:
            result["subprocess_invoked"] = True
            completed = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            result["subprocess"] = {
                "returncode": completed.returncode,
                "stdout_tail": completed.stdout[-2000:],
                "stderr_tail": completed.stderr[-2000:],
            }
            result["checks"]["subprocess_exit_zero"] = (
                completed.returncode == 0
            )
        except subprocess.TimeoutExpired as exc:
            result["subprocess"] = {
                "returncode": None,
                "reason": "timeout",
                "stdout_tail": (
                    (exc.stdout or "")[-2000:]
                    if isinstance(exc.stdout, str)
                    else ""
                ),
                "stderr_tail": (
                    (exc.stderr or "")[-2000:]
                    if isinstance(exc.stderr, str)
                    else ""
                ),
            }
            result["checks"]["subprocess_exit_zero"] = False
        except OSError as exc:
            result["subprocess"] = {
                "returncode": None,
                "reason": type(exc).__name__,
                "stdout_tail": "",
                "stderr_tail": str(exc)[-2000:],
            }
            result["checks"]["subprocess_exit_zero"] = False

    artifacts_to_validate = (
        [replay_rel] if replay_rel is not None else distributed_artifacts
    )
    artifact_results = [
        _artifact_result(rel) for rel in artifacts_to_validate
    ]
    result["validated_artifacts"] = artifacts_to_validate
    result["artifacts"] = artifact_results
    result["checks"]["artifact_semantics_pass"] = (
        bool(artifact_results)
        and all(item["ok"] for item in artifact_results)
    )

    if not static_only:
        after_hashes = _hash_artifacts(distributed_artifacts)
        result["distributed_artifact_hashes"] = {
            "before": before_hashes,
            "after": after_hashes,
        }
        result["checks"]["distributed_artifacts_immutable"] = (
            before_hashes == after_hashes
            and set(before_hashes) == set(distributed_artifacts)
        )

    if replay_target is not None:
        try:
            expected_runtime_parent = (
                ROOT.resolve() / "artifacts" / ".verify"
            )
            if (
                replay_target.parent.is_symlink()
                or replay_target.parent.resolve()
                != expected_runtime_parent
            ):
                raise RuntimeError("unsafe_runtime_artifact_parent")
            replay_target.unlink(missing_ok=True)
            try:
                replay_target.parent.rmdir()
            except OSError:
                pass
        except (OSError, RuntimeError, UnicodeError) as exc:
            result["runtime_artifact_cleanup_error"] = (
                f"{type(exc).__name__}: {exc}"
            )
            result["checks"]["runtime_artifact_cleaned"] = False
        else:
            result["checks"]["runtime_artifact_cleaned"] = (
                not replay_target.exists()
            )

    result["pass"] = all(result["checks"].values())
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument(
        "--out",
        "--output",
        dest="output",
        type=Path,
        default=DEFAULT_OUT,
    )
    return parser.parse_args()


def _prepare_output_path(output: Path) -> tuple[bool, Path]:
    candidate = output if output.is_absolute() else ROOT / output
    try:
        lexical = candidate.absolute()
        root_lexical = ROOT.absolute()
        resolved = candidate.resolve()
        root_resolved = ROOT.resolve()
    except (OSError, RuntimeError, UnicodeError):
        return False, candidate

    if lexical.is_relative_to(root_lexical):
        if lexical != DEFAULT_OUT.absolute():
            return False, lexical
        rel = lexical.relative_to(root_lexical).as_posix()
        try:
            expected_parent = root_resolved / "artifacts"
            if candidate.parent.resolve() != expected_parent:
                return False, lexical
            if not _ignored_by_fallback(rel, _gitignore_patterns()):
                return False, lexical
            if (ROOT / ".git").exists():
                tracked = subprocess.run(
                    [
                        "git",
                        "-C",
                        str(ROOT),
                        "ls-files",
                        "--error-unmatch",
                        "--",
                        rel,
                    ],
                    capture_output=True,
                    check=False,
                )
                if tracked.returncode != 1:
                    return False, lexical
        except (OSError, RuntimeError, UnicodeError):
            return False, lexical
    elif resolved.is_relative_to(root_resolved):
        return False, resolved

    try:
        if candidate.is_dir():
            return False, lexical
        if candidate.exists() or candidate.is_symlink():
            candidate.unlink()
    except (OSError, RuntimeError, UnicodeError):
        return False, lexical
    return True, lexical

def main() -> int:
    args = parse_args()
    output_allowed, output = _prepare_output_path(args.output)
    if not output_allowed:
        print(
            "Verifier output inside the package must use "
            "artifacts/public_verify_result.json.",
            file=sys.stderr,
        )
        return 2

    manifest_ok, manifest_results, manifest_detail = verify_manifest(
        MANIFEST_PATH
    )
    release_ok, release_results, release_detail = (
        verify_release_checksum(RELEASE_PATH)
    )
    preflight_ok = manifest_ok and release_ok

    routes: list[dict[str, Any]] = []
    route_validations: list[dict[str, Any]] = []
    route_schema_ok = False
    coverage_ok = False
    if not preflight_ok:
        route_error: str | None = "preflight_integrity_failed"
    else:
        try:
            route_document = load_routes()
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            route_error = type(exc).__name__
        else:
            (
                route_schema_ok,
                coverage_ok,
                routes,
                route_validations,
                route_error,
            ) = validate_route_document(route_document)

    route_results: list[dict[str, Any]] = []
    if preflight_ok and route_schema_ok and coverage_ok:
        route_results = [
            run_route(
                route,
                static_only=args.static_only,
                timeout=args.timeout,
            )
            for route in routes
        ]
    routes_ok = bool(route_results) and all(
        item["pass"] for item in route_results
    )

    (
        post_manifest_ok,
        post_manifest_results,
        post_manifest_detail,
    ) = verify_manifest(MANIFEST_PATH)
    (
        post_release_ok,
        post_release_results,
        post_release_detail,
    ) = verify_release_checksum(RELEASE_PATH)

    passed = (
        preflight_ok
        and route_schema_ok
        and coverage_ok
        and routes_ok
        and post_manifest_ok
        and post_release_ok
    )
    envelope = {
        "schema_version": 3,
        "status": (
            "PASS_PUBLIC_REPLAY_ENVELOPE"
            if passed
            else "FAIL_PUBLIC_REPLAY_ENVELOPE"
        ),
        "pass": passed,
        "mode": "static_only" if args.static_only else "replay",
        "checks": {
            "manifest_preflight_pass": manifest_ok,
            "release_checksum_preflight_pass": release_ok,
            "manifest_entries_unique": manifest_detail["checks"][
                "entries_unique"
            ],
            "manifest_coverage_exact": (
                manifest_detail["checks"]["coverage_complete"]
                and manifest_detail["checks"]["no_extra_entries"]
            ),
            "route_schema_pass": route_schema_ok,
            "coverage_exact": coverage_ok,
            "all_routes_pass": routes_ok,
            "manifest_postflight_pass": post_manifest_ok,
            "release_checksum_postflight_pass": post_release_ok,
        },
        "counts": {
            "manifest_entries": manifest_detail["declared_entries"],
            "distributed_files": manifest_detail["distributed_files"],
            "routes_declared": len(routes),
            "routes_evaluated": len(route_results),
            "routes_invoked": sum(
                item.get("subprocess_invoked") is True
                for item in route_results
            ),
            "required_routes": len(REQUIRED_ROUTE_IDS),
        },
        "route_error": route_error,
        "route_validations": route_validations,
        "routes": route_results,
        "release_checksum_preflight": {
            "detail": release_detail,
            "entries": release_results,
        },
        "manifest_preflight": {
            "coverage": manifest_detail,
            "entries": manifest_results,
        },
        "release_checksum_postflight": {
            "detail": post_release_detail,
            "entries": post_release_results,
        },
        "manifest_postflight": {
            "coverage": post_manifest_detail,
            "entries": post_manifest_results,
        },
        "boundary": {
            "x13": (
                "human proof and classical source lock; "
                "no standalone numerical replay"
            ),
            "g004_cpl001": (
                "classical source-coupling guardrail; human proof and "
                "sources; no numerical replay or novelty"
            ),
            "x05_full_census": (
                "optional offline/Colab regeneration, "
                "not part of the default verifier"
            ),
            "governance": (
                "current public envelope; historical internal gate "
                "metadata are evidence only"
            ),
        },
    }
    write_allowed, prepared_output = _prepare_output_path(output)
    if not write_allowed or prepared_output != output:
        print(
            "Verifier output became unsafe before envelope write.",
            file=sys.stderr,
        )
        return 2

    temporary_output: Path | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=output.parent,
            prefix=".public_verify_result.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(envelope, handle, indent=2, sort_keys=True)
            handle.write("\n")
            temporary_output = Path(handle.name)
        os.replace(temporary_output, output)
        temporary_output = None
    except (OSError, RuntimeError, UnicodeError) as exc:
        print(
            f"Unable to write verifier envelope: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2
    finally:
        if temporary_output is not None:
            try:
                temporary_output.unlink(missing_ok=True)
            except OSError:
                pass

    print(
        json.dumps(
            {
                "pass": passed,
                "status": envelope["status"],
                "mode": envelope["mode"],
                "routes_evaluated": len(route_results),
                "routes_invoked": envelope["counts"]["routes_invoked"],
                "output": str(output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
