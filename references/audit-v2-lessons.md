# NonFiction-Book-Pipeline-Kanban v2 Audit Lessons

Session-derived audit notes for making the book pipeline mechanically reliable.

## Main finding

The first version captured a successful manual run, but it was not safe as a reusable automated pipeline. The reliable class-level strategy is:

```text
official CLI + HERMES_KANBAN_BOARD + --json + --parent + --idempotency-key + QA gates + validator scripts
```

## Loopholes found

1. **Raw SQLite task creation is unsafe for normal automation**
   - Current schema uses `tasks.created_at INTEGER`; hand inserts with SQL datetime are wrong.
   - Future migrations can add required columns.
   - Fix: create tasks via `hermes kanban create --json`.

2. **Flat task lists are unsafe**
   - Assembly/Final Edit can run before chapters exist.
   - Fix: create real parent dependencies.

3. **`boards switch` is not an automation primitive**
   - It is useful interactively but unreliable across subprocess/batch command boundaries.
   - Fix: pass `HERMES_KANBAN_BOARD=<slug>` for every scripted Kanban command.

4. **`hermes kanban dispatch run --board ...` is invalid**
   - `dispatch` is a one-pass command; no `run` subcommand.
   - Fix: use `HERMES_KANBAN_BOARD=<board> hermes kanban dispatch --dry-run` for verification; use `hermes gateway run` for long-running runtime.

5. **Placeholder intake can be mistaken for real content**
   - Fix: require `--synopsis-file` for production runs or block dispatch until placeholder text is replaced.

6. **No research stage weakens nonfiction reliability**
   - Fix: add Research before Foundation, with source map, factual spine, and risk register outputs.

7. **Writer freedom creates chapter drift**
   - Fix: Foundation must produce `05-chapter-briefs.md`; wave tasks must follow it.

8. **No objective completion check**
   - Fix: add Pre-Assembly QA, Final QA, and `scripts/validate-project.py`.

9. **Final edit can damage manuscript**
   - Fix: require checkpoint before assembly/final edit.

10. **Source Audit is useful but should not be mandatory**
   - Problem: strict source-first workflow creates friction for users who just want to provide a synopsis and let agents research.
   - Fix: make Source Audit explicit and optional with `--source-mode user|agent|none`.
   - `user`: require `<project>/sources/` files or `<project>/sources/urls.txt`; create `Source Audit (user)` before Research.
   - `agent`: default; create `Source Audit (agent)` before Research; researcher must find and cross-check web sources.
   - `none`: skip separate Source Audit; Research remains first and mandatory.

11. **Agent-led web research can overtrust weak sources**
   - Fix: Source Audit(agent) must output `research/00-source-audit.md` and `research/00-source-claims.tsv`.
   - Important claims should be cross-checked against at least two independent sources where feasible.
   - Uncertain claims must be marked explicitly rather than smoothed into confident prose.

12. **User-source mode can silently fall back to agent assumptions**
   - Fix: `--source-mode user` must fail fast if neither `<project>/sources/` files nor `<project>/sources/urls.txt` exists.

13. **Validator must track source mode**
   - Fix: `validate-project.py` reads `intake.source_mode`.
   - In `agent`/`user` modes it errors on missing `research/00-source-audit.md` and warns on missing `research/00-source-claims.tsv`.
   - In `none` mode it does not require source-audit artifacts.

## Factually tested commands

Temporary-board tests confirmed dependency behavior and Source Audit mode behavior.

Dependency test:

```bash
HERMES_KANBAN_BOARD=<board> hermes kanban create "A parent" --assignee analyst --body "body" --idempotency-key test-parent --json
HERMES_KANBAN_BOARD=<board> hermes kanban create "B child" --assignee writer --body "body" --parent <parent_id> --idempotency-key test-child --json
HERMES_KANBAN_BOARD=<board> hermes kanban dispatch --dry-run
```

Observed:

```text
parent: ready
child: todo
spawnable in dry-run: parent only
```

Source-mode tests:

```bash
python3 scripts/init-project.py "Agent Book" /tmp/book --source-mode agent --allow-placeholder --skip-profiles
HERMES_KANBAN_BOARD=<board> hermes kanban dispatch --dry-run
# Observed: Source Audit (agent) is the only spawnable task.

python3 scripts/init-project.py "None Book" /tmp/book --source-mode none --allow-placeholder --skip-profiles
HERMES_KANBAN_BOARD=<board> hermes kanban dispatch --dry-run
# Observed: Research is the only spawnable task; no Source Audit card exists.

python3 scripts/init-project.py "User Book" /tmp/book --source-mode user --allow-placeholder --skip-profiles
# Observed without sources/: fails fast.

mkdir -p /tmp/book/sources && echo 'https://example.com/source' > /tmp/book/sources/urls.txt
python3 scripts/init-project.py "User Book" /tmp/book --source-mode user --allow-placeholder --skip-profiles
# Observed: Source Audit (user) is the only initial ready task.
```

Validator tests:

```text
source_mode=agent without research/00-source-audit.md → ERROR
source_mode=none without source audit artifacts → OK
source_mode=agent with 00-source-audit.md + 00-source-claims.tsv → OK
```

## Correct confidence framing

Do not claim “100% confidence” in literary quality or factual truth. The defensible claim is:

> High confidence in the mechanical automation strategy after tests; factual quality still requires source audit, review, and validation.
