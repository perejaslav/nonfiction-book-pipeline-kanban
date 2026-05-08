---
name: nonfiction-book-pipeline-kanban
description: >
  Автоматизированный pipeline для написания научно-популярной книги через Hermes Kanban:
  проект, доска, профили, dependency graph, исследование, foundation, волны глав,
  QA-gates, детерминированная сборка manuscript, финальное ревью и валидация.
version: 2.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [kanban, book-writing, multi-agent, nonfiction, pipeline, automation]
    related_skills: [kanban-orchestrator, kanban-worker, nonfiction-book-pipeline]
---

# NonFiction-Book-Pipeline-Kanban

## Pipeline routing rule

There are two related skills:

1. `nonfiction-book-pipeline-kanban` — default router for **new end-to-end book projects** from natural-language commands.
2. `nonfiction-book-pipeline` — classic NFP engine for delegate_task-only writing, fallback, existing manuscript editing, micro-final passes, export, and detailed editorial protocols.

Use this Kanban skill by default when the user says:

- “Напиши книгу о …”
- “Вот план, сделай книгу”
- “Хочу научпоп на 60–80 тысяч слов”
- “Источники найди сам”
- “Работай по этим источникам”
- “Запусти процесс / pipeline написания книги”

Use classic `nonfiction-book-pipeline` instead when:

- the user explicitly says “без Kanban”, “NFP-only”, “через субагентов без доски”;
- Kanban/gateway is broken and immediate fallback is needed;
- the task is not starting a new book, but editing an existing manuscript;
- the task is micro-final patching, fact-check pass, PDF/EPUB export, or publication cleanup;
- the user asks for sequential safe mode.

Explicit user instruction has absolute priority:

```text
User says “используй Kanban / через Kanban / Kanban pipeline” → MUST use nonfiction-book-pipeline-kanban.
User says “не используй Kanban / без Kanban / NFP-only / без доски” → MUST NOT use this skill; use classic nonfiction-book-pipeline.
```

If both skills match and there is no explicit Kanban/no-Kanban instruction, route by intent:

```text
new full book from topic/plan/synopsis → nonfiction-book-pipeline-kanban
existing manuscript / editorial repair / export → nonfiction-book-pipeline
explicit no-Kanban → nonfiction-book-pipeline
explicit Kanban → nonfiction-book-pipeline-kanban
```

Do not override an explicit user choice because another skill looks more convenient. The Kanban skill may still borrow editorial rules from classic NFP after the manuscript exists; the routing decision only determines the orchestration engine.

## Overview

Use this skill when the user wants to write a long-form nonfiction / popular-science book through durable Hermes Kanban orchestration.

**Primary interaction model: natural-language user command.** The user should not need to know, type, or understand terminal commands, Kanban terminology, board slugs, `--source-mode`, scripts, or Hermes internals. The user can simply say what book they want, paste a synopsis/plan/sources, or point to files. The agent/operator must translate that into the correct setup, commands, board, tasks, monitoring, validation, and final report.

Terminal commands in this skill are **operator instructions for the agent**, not instructions to push onto the user by default. Only show commands if the user explicitly asks for them or wants to run something manually.

The pipeline is intentionally **not** just “create 9 cards and hope”. It must be:

1. **Automated** — one init script creates project folders, board, and cards.
2. **Dependency-gated** — downstream tasks cannot start before parent artifacts exist.
3. **Source-aware by choice** — optional Source Audit can use user-provided `sources/` / `sources/urls.txt`, agent-led web research, or be skipped.
4. **Validated** — QA cards and validation scripts check files, placeholders, chapter counts, source-audit outputs, and word count.
5. **Reproducible** — task creation uses the official `hermes kanban create --json --parent --idempotency-key` interface, not raw SQLite.
6. **Recoverable** — manuscript backups are required before assembly/final edit.

## Confidence statement

Current strategy after v2/v2.1 fixes: **high confidence for automation mechanics** on this Hermes install, because the critical assumptions were tested:

- `HERMES_KANBAN_BOARD=<slug> hermes kanban create ... --json` works.
- `--parent <task_id>` creates real dependency gating: parent becomes `ready`, child stays `todo`.
- `--idempotency-key` prevents duplicate tasks.
- `hermes kanban dispatch --board` is not used; board is passed via `HERMES_KANBAN_BOARD`.

Not “mathematically 100%” for literary quality or factual truth — no automated pipeline can guarantee that. The right target is: **100% explicit mechanical strategy + verifiable gates + honest failure modes**.

## When to Use

Use when:

- The book is 30k–100k+ words.
- Several roles are useful: researcher, analyst, writer, reviewer.
- The work may take hours and should survive retries/restarts.
- The user wants a repeatable pipeline for future books.

Do not use when:

- The user wants a short essay/article.
- The topic requires strict academic citation audit beyond the current source material.
- The user has not provided even a minimal synopsis.

## Natural-language operating contract

When the user says something like:

- “Напиши книгу о Трапезундской империи”
- “Вот план, сделай из этого книгу”
- “Хочу научпоп на 70 тысяч слов, источники найдёшь сам”
- “Вот список источников/URL, работай по ним”

The agent should proceed as operator:

1. Infer or briefly ask for missing essentials only if truly necessary: title/topic, approximate scope, source preference.
2. If the user supplied sources/URLs in chat, save them into the project `sources/` area automatically.
3. Pick source mode:
   - explicit user sources → `user`;
   - no sources, user delegates research → `agent`;
   - user asks for quick/light draft → `none`.
4. Run the init script and Kanban setup internally.
5. Monitor the board and repair operational failures.
6. Validate artifacts before telling the user the book is done.
7. Report in plain Russian: what was created, where the files are, current status, and what decision/input is needed next.

Do **not** answer with “run this command” as the main response unless the user explicitly asks for manual commands.

## One-command initialization

```bash
# User provides sources in ~/my-book/sources/ or ~/my-book/sources/urls.txt
python3 ~/.hermes/skills/nonfiction-book-pipeline-kanban/scripts/init-project.py \
  "Название книги" ~/my-book \
  --synopsis-file ~/synopsis.md \
  --source-mode user

# Agent finds and cross-checks sources on the web (default)
python3 ~/.hermes/skills/nonfiction-book-pipeline-kanban/scripts/init-project.py \
  "Название книги" ~/my-book \
  --synopsis-file ~/synopsis.md \
  --source-mode agent

# Lightweight mode: skip separate Source Audit, still do basic Research
python3 ~/.hermes/skills/nonfiction-book-pipeline-kanban/scripts/init-project.py \
  "Название книги" ~/my-book \
  --synopsis-file ~/synopsis.md \
  --source-mode none
```

If no synopsis file is provided, the script creates `intake.json` with a placeholder. Do **not** dispatch until the placeholder is replaced.

Validate setup:

```bash
HERMES_KANBAN_BOARD=my-book hermes kanban list
HERMES_KANBAN_BOARD=my-book hermes kanban dispatch --dry-run
```

Start runtime:

```bash
hermes gateway run
```

Current Hermes runs Kanban dispatcher inside the gateway by default. `hermes kanban daemon` is deprecated; `hermes kanban dispatch` is a one-pass command.

## Project structure

```text
~/my-book/
├── intake.json
├── research/
│   ├── 01-source-map.md
│   ├── 02-factual-spine.md
│   └── 03-risk-register.md
├── foundation/
│   ├── 01-structure.md
│   ├── 02-facts.md
│   ├── 03-voice.md
│   ├── 04-terms.md
│   └── 05-chapter-briefs.md
├── chapters/
│   ├── 01-*.md
│   └── 21-*.md
├── reports/
│   ├── pre-assembly-qa.md
│   ├── assembly-report.md
│   ├── final-edit-report.md
│   └── validation-*.md
├── checkpoints/
│   ├── manuscript-before-assembly.md
│   └── manuscript-before-final-edit.md
└── manuscript.md
```

## Dependency graph

```text
Source Audit (optional researcher; mode=user|agent)
  ↓
Research (researcher)
  ↓
Foundation (analyst)
  ↓
Wave 1 ─┐
Wave 2 ─┤
Wave 3 ─┤ writer, parallel after Foundation
Wave 4 ─┘
  ↓
Expansion (writer)
  ↓
Pre-Assembly QA (reviewer)
  ↓
Assembly (default)
  ↓
Final Edit (reviewer)
  ↓
Final QA (reviewer)
```

The init script creates this graph with `--parent` dependencies. This is mandatory. A flat task list is a bug: assembly/review can start too early.

## Roles

| Profile | Responsibility |
|---|---|
| `researcher` | Optional Source Audit, source map, factual spine, risk register |
| `analyst` | Structure, chapter briefs, facts/terms/voice |
| `writer` | Draft chapter waves and reference apparatus |
| `reviewer` | QA gates, final edit, final validation |
| `default` | Deterministic assembly / mechanical tasks |

Profiles should be created with `hermes profile create <name> --clone` so config/model/env are inherited. Do not rely on `hermes profile create researcher writer analyst` — CLI creates one profile at a time.

## Required task creation rules

Always use official CLI:

```bash
HERMES_KANBAN_BOARD=my-book hermes kanban create "Task title" \
  --assignee writer \
  --body "..." \
  --parent t_parent_id \
  --idempotency-key "nfp-kanban:my-book:task-title" \
  --max-runtime 3h \
  --skill nonfiction-book-pipeline-kanban \
  --json
```

Do **not** write directly into SQLite unless repairing a corrupted/misplaced board manually. Direct SQLite is schema-fragile: `tasks.created_at` is INTEGER, not text datetime, and future migrations can add required fields.

## Validation

Manual validation command:

```bash
python3 ~/.hermes/skills/nonfiction-book-pipeline-kanban/scripts/validate-project.py ~/my-book --stage all
```

It checks:

- `intake.json` exists and parses.
- foundation has 5 required files.
- chapter count is high enough.
- chapters are not empty.
- bad placeholders are absent.
- source-audit outputs exist when `source_mode` is `user` or `agent`.
- manuscript has frontmatter.
- word count is near target.

## Known loopholes and fixes

### 1. Flat task list lets later phases start too early

Fix: use `--parent` dependencies. The v2 init script does this.

### 2. Raw SQLite task creation is schema-fragile

Fix: use `hermes kanban create --json`. The v2 init script does this. SQLite is only for forensic repair.

### 3. Placeholder synopsis can be treated as real input

Fix: `init-project.py` refuses to proceed unless `--allow-placeholder` is used or a real `--synopsis-file` is provided. Do not dispatch placeholder projects.

### 4. `--board` is unreliable in subprocess contexts

Fix: pass `HERMES_KANBAN_BOARD=<slug>` in the environment for every command. This was factually tested.

### 5. `hermes kanban dispatch run --board` is invalid

Fix: use either:

```bash
HERMES_KANBAN_BOARD=my-book hermes kanban dispatch --dry-run
hermes gateway run
```

or one-pass:

```bash
HERMES_KANBAN_BOARD=my-book hermes kanban dispatch --max 3
```

### 6. `hermes kanban daemon` is deprecated

Fix: gateway is the long-running runtime. Use daemon only if explicitly needed and knowingly accepting deprecation.

### 7. “writer writes arbitrary chapters” risk

Fix: Foundation must produce `05-chapter-briefs.md`; wave tasks must follow those briefs.

### 8. No research stage

Fix: v2 adds mandatory `Research` before Foundation.

### 9. Reviewer edits without backup

Fix: final edit task must copy `manuscript.md` to `checkpoints/manuscript-before-final-edit.md` before editing.

### 10. No objective completion test

Fix: final QA task plus `validate-project.py`.

### 11. Source Audit should not be mandatory for every user

Fix: v2.1 adds `--source-mode user|agent|none`.

- `user`: requires files in `<project>/sources/` or `<project>/sources/urls.txt`; creates `Source Audit (user)` before Research.
- `agent`: default; creates `Source Audit (agent)` where researcher must find and cross-check web sources.
- `none`: skips separate Source Audit; Research remains mandatory but lighter.

### 12. Agent-led web research can hallucinate or overtrust weak sources

Fix: `Source Audit (agent)` must produce `research/00-source-audit.md` and `research/00-source-claims.tsv`, cross-check important claims where possible, and mark uncertainty. Validator warns/errors if source-audit outputs are missing in `agent`/`user` modes.

## Operational loop

When using this skill:

1. Create project with `scripts/init-project.py`.
2. Confirm `intake.json` is real, not placeholder.
3. Confirm graph:
   ```bash
   HERMES_KANBAN_BOARD=<board> hermes kanban list
   ```
4. Dry-run dispatcher:
   ```bash
   HERMES_KANBAN_BOARD=<board> hermes kanban dispatch --dry-run
   ```
5. Start gateway:
   ```bash
   hermes gateway run
   ```
6. Monitor:
   ```bash
   HERMES_KANBAN_BOARD=<board> hermes kanban list
   HERMES_KANBAN_BOARD=<board> hermes kanban runs <task_id>
   HERMES_KANBAN_BOARD=<board> hermes kanban log <task_id>
   ```
7. Validate artifacts before declaring done:
   ```bash
   python3 ~/.hermes/skills/nonfiction-book-pipeline-kanban/scripts/validate-project.py <project> --stage all
   ```

## Verification Checklist

- [ ] `init-project.py --help` runs.
- [ ] `validate-project.py --help` runs.
- [ ] task creation uses `HERMES_KANBAN_BOARD`, not `--board`.
- [ ] task creation uses `--parent` dependencies.
- [ ] task creation uses `--idempotency-key`.
- [ ] no raw SQLite insert is used in the normal path.
- [ ] Research precedes Foundation.
- [ ] Foundation produces `05-chapter-briefs.md`.
- [ ] QA precedes Assembly.
- [ ] Assembly precedes Final Edit.
- [ ] Final QA runs after Final Edit.
- [ ] Source Audit mode is explicit: `user`, `agent`, or `none`.
- [ ] In `user` mode, `<project>/sources/` or `<project>/sources/urls.txt` exists before board creation.
- [ ] In `agent` mode, first ready task is `Source Audit (agent)`.
- [ ] In `none` mode, no Source Audit task is created and Research is first ready.
- [ ] Validator checks source-audit outputs for `user`/`agent` modes.
- [ ] backups are required before destructive manuscript edits.

## Supporting files

- `scripts/init-project.py` — robust initializer.
- `scripts/validate-project.py` — artifact validator.
- `templates/intake-template.json` — intake template.
- `references/kanban-setup.md` — expanded setup notes.
- `references/audit-v2-lessons.md` — session-derived loopholes, tested fixes, and confidence framing.
