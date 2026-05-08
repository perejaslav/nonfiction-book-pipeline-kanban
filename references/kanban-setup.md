# Kanban + NonFiction Pipeline — First-Time Setup v2

## Core rule

Normal automation path must use the official CLI:

```bash
HERMES_KANBAN_BOARD=<board> hermes kanban create ... --json --parent ... --idempotency-key ...
```

Do not use direct SQLite inserts for normal task creation. SQLite is acceptable only for forensic repair or migration after a CLI limitation is confirmed.

## Setup checklist

```text
1. Prepare synopsis.md
2. Run init-project.py with explicit source mode
3. Inspect intake.json
4. Inspect board dependency graph
5. Dry-run dispatch
6. Start gateway runtime
7. Monitor board
8. Validate artifacts
```

## 1. Prepare synopsis

Create a plain text or Markdown synopsis:

```bash
nano ~/synopsis.md
```

It should include:

- working title;
- central thesis;
- audience;
- target tone;
- approximate size;
- desired chapters/parts;
- forbidden claims or style constraints.

## 2. Initialize project

```bash
# Default: agent performs web research and cross-checking
python3 ~/.hermes/skills/nonfiction-book-pipeline-kanban/scripts/init-project.py \
  "Название книги" ~/my-book \
  --synopsis-file ~/synopsis.md \
  --source-mode agent

# User-supplied sources mode: requires ~/my-book/sources/ files or urls.txt
mkdir -p ~/my-book/sources
nano ~/my-book/sources/urls.txt
python3 ~/.hermes/skills/nonfiction-book-pipeline-kanban/scripts/init-project.py \
  "Название книги" ~/my-book \
  --synopsis-file ~/synopsis.md \
  --source-mode user

# Lightweight mode: skip separate Source Audit
python3 ~/.hermes/skills/nonfiction-book-pipeline-kanban/scripts/init-project.py \
  "Название книги" ~/my-book \
  --synopsis-file ~/synopsis.md \
  --source-mode none
```

The script:

- creates project directories;
- creates/uses a Kanban board named from the project directory;
- creates required profiles if missing using `--clone`;
- creates a real dependency graph;
- uses `--idempotency-key` to avoid duplicate cards.

## 3. Inspect intake

```bash
python3 -m json.tool ~/my-book/intake.json
```

Do not dispatch if synopsis contains placeholder text.

## 4. Inspect board

```bash
HERMES_KANBAN_BOARD=my-book hermes kanban list
```

Expected initial state for `--source-mode agent` or `user`:

```text
Source Audit                     ready
Research                         todo
Foundation                       todo
```

Expected initial state for `--source-mode none`:

```text
Research                         ready
Foundation                       todo
```

All later tasks should be `todo` until their parents complete.

## 5. Dry-run dispatch

```bash
HERMES_KANBAN_BOARD=my-book hermes kanban dispatch --dry-run
```

Expected: only `Source Audit` is spawnable initially in `agent`/`user` mode; only `Research` is spawnable in `none` mode.

## 6. Start runtime

Current Hermes: dispatcher runs inside the gateway by default.

```bash
hermes gateway run
```

If you explicitly need one-pass dispatch:

```bash
HERMES_KANBAN_BOARD=my-book hermes kanban dispatch --max 3
```

Avoid:

```bash
hermes kanban dispatch run --board my-book   # invalid
hermes kanban daemon                         # deprecated unless you know why
```

## 7. Monitor

```bash
HERMES_KANBAN_BOARD=my-book hermes kanban list
HERMES_KANBAN_BOARD=my-book hermes kanban runs <task_id>
HERMES_KANBAN_BOARD=my-book hermes kanban log <task_id>
HERMES_KANBAN_BOARD=my-book hermes kanban show <task_id>
```

## 8. Validate artifacts

```bash
python3 ~/.hermes/skills/nonfiction-book-pipeline-kanban/scripts/validate-project.py ~/my-book --stage all
```

The validator writes reports under:

```text
~/my-book/reports/validation-all.md
```

## Troubleshooting

### `--board` behavior

Top-level `hermes kanban --board <slug>` exists, but for automation prefer environment variable:

```bash
HERMES_KANBAN_BOARD=<slug> hermes kanban list
```

This avoids argument-order/subprocess ambiguity.

### Profile missing model

Create profiles with clone:

```bash
hermes profile create writer --clone
```

If already created empty, compare:

```bash
hermes profile show writer
hermes profile show default
```

Then repair manually by copying config/env from a known-good profile.

### Dispatcher seems idle

Check what is ready:

```bash
HERMES_KANBAN_BOARD=<board> hermes kanban dispatch --dry-run
```

If no tasks are ready, inspect parent task statuses:

```bash
HERMES_KANBAN_BOARD=<board> hermes kanban show <task_id>
```

### Assembly started too early

This means dependencies were not created. The normal graph is:

```text
Research → Foundation → Waves → Expansion → QA → Assembly → Final Edit → Final QA
```

Recreate with `init-project.py` or manually add links:

```bash
HERMES_KANBAN_BOARD=<board> hermes kanban link <parent_id> <child_id>
```

### Final edit damaged manuscript

Recover from checkpoint:

```bash
cp ~/my-book/checkpoints/manuscript-before-final-edit.md ~/my-book/manuscript.md
```

### Word count too low

Create a new Expansion task linked from Final QA findings. Do not manually declare success.
