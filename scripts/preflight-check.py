#!/usr/bin/env python3
"""Preflight check and repair for NonFiction-Book-Pipeline-Kanban.

Goals:
- verify required profiles exist and have a model
- clone/fix missing profiles when possible
- verify Kanban runtime is reachable
- report issues without aborting installation

This is intentionally non-blocking: it repairs what it can and prints
clear warnings for anything that still needs manual attention.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REQUIRED_PROFILES = ["researcher", "analyst", "writer", "reviewer", "default"]


def sh(args: list[str], check: bool = False) -> subprocess.CompletedProcess:
    r = subprocess.run(args, text=True, capture_output=True)
    if check and r.returncode != 0:
        print("FAILED:", " ".join(args), file=sys.stderr)
        print(r.stdout, file=sys.stderr)
        print(r.stderr, file=sys.stderr)
    return r


def profile_has_model(profile: str) -> bool:
    r = sh(["hermes", "profile", "show", profile])
    return r.returncode == 0 and ("model" in r.stdout.lower())


def profile_exists(profile: str) -> bool:
    r = sh(["hermes", "profile", "show", profile])
    return r.returncode == 0


def ensure_profile(profile: str, clone_from: str = "researcher") -> tuple[bool, str]:
    """Return (ok, note)."""
    if profile_exists(profile) and profile_has_model(profile):
        return True, "ok"

    # Try create or clone if missing / incomplete.
    if not profile_exists(profile):
        r = sh(["hermes", "profile", "create", profile, "--clone"], check=False)
        if r.returncode == 0:
            return profile_has_model(profile), "created via --clone"
        # fallback: create empty then attempt to clone manually by repair path below

    # If the profile exists but has no model, try manual clone via config copy.
    src = Path.home() / ".hermes" / "profiles" / clone_from
    dst = Path.home() / ".hermes" / "profiles" / profile
    if src.exists() and dst.exists():
        for name in ["config.yaml", ".env", "auth.json"]:
            sp = src / name
            if sp.exists():
                (dst / name).write_bytes(sp.read_bytes())
        return profile_has_model(profile), f"repaired by copying {clone_from}"

    return False, "needs manual attention"


def kanban_runtime_ok() -> bool:
    # Check that the CLI exists and can list boards.
    r = sh(["hermes", "kanban", "boards", "list"])
    return r.returncode == 0


def main() -> int:
    issues = []
    repaired = []

    for profile in REQUIRED_PROFILES:
        ok, note = ensure_profile(profile)
        if ok:
            if note != "ok":
                repaired.append(f"{profile}: {note}")
        else:
            issues.append(f"profile '{profile}' missing or has no model ({note})")

    if kanban_runtime_ok():
        print("Kanban runtime: OK")
    else:
        issues.append("Kanban runtime is not reachable via `hermes kanban boards list`")

    if repaired:
        print("Repaired:")
        for x in repaired:
            print(" -", x)

    if issues:
        print("Warnings:")
        for x in issues:
            print(" -", x)
        print("\nNon-blocking preflight finished with warnings.")
        return 0

    print("Preflight OK: all required profiles present with models; Kanban runtime reachable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
