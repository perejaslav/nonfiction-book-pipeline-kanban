# Soft preflight for first install / new machine

This reference documents the soft-preflight behavior added to the Kanban book pipeline.

## Purpose

When the skill is installed on a new machine, the initializer should not hard-fail just because a profile is missing or a runtime component is not yet configured. It should:

1. Check required profiles:
   - `researcher`
   - `analyst`
   - `writer`
   - `reviewer`
   - `default`
2. Check whether each profile has a model.
3. Try to repair missing profiles automatically when possible:
   - `hermes profile create <name> --clone`
   - fallback: copy `config.yaml`, `.env`, `auth.json` from `researcher`
4. Check that Kanban runtime is reachable via `hermes kanban boards list`.
5. Print warnings for anything still missing instead of aborting installation.

## Intended behavior

- Soft preflight is a setup aid, not a blocker.
- If repair succeeds, continue.
- If repair fails, continue with a clear warning so the user knows what to fix.

## Files involved

- `scripts/preflight-check.py`
- `scripts/init-project.py`

## Notes

The preflight is meant to reduce first-run friction on a new computer. It does not guarantee that the Hermes environment is fully healthy; it only repairs the common missing-profile / missing-model cases that were actually encountered during the Trapezund setup.
