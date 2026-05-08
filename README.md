# NonFiction Book Pipeline Kanban

A Hermes Agent skill for writing long-form nonfiction and popular-science books through durable Kanban orchestration.

This skill lets a user give a natural-language book request, synopsis, plan, or source list while Hermes handles the operational work: project setup, Kanban board creation, task graph, researcher/analyst/writer/reviewer profiles, source audit, drafting waves, QA gates, deterministic manuscript assembly, final edit, and validation.

## What it does

- Creates a complete book project structure.
- Creates a Hermes Kanban board and dependency-gated task graph.
- Supports optional Source Audit modes:
  - `user` — use files in `sources/` or URLs in `sources/urls.txt`.
  - `agent` — researcher finds and cross-checks web sources. Default.
  - `none` — skip separate Source Audit for lighter drafts.
- Uses official Hermes Kanban CLI with `HERMES_KANBAN_BOARD`, `--json`, `--parent`, and `--idempotency-key`.
- Avoids raw SQLite task creation in the normal path.
- Adds QA gates before assembly and final delivery.
- Includes validation scripts for artifacts, placeholders, chapter counts, source-audit outputs, and word count.

## Pipeline graph

```text
Source Audit (optional: user|agent)
  ↓
Research
  ↓
Foundation
  ↓
Wave 1 ─┐
Wave 2 ─┤
Wave 3 ─┤
Wave 4 ─┘
  ↓
Expansion
  ↓
Pre-Assembly QA
  ↓
Assembly
  ↓
Final Edit
  ↓
Final QA
```

## Installation

Install directly into your Hermes Agent skills directory:

```bash
mkdir -p ~/.hermes/skills/nonfiction-book-pipeline-kanban
git clone https://github.com/perejaslav/nonfiction-book-pipeline-kanban.git \
  ~/.hermes/skills/nonfiction-book-pipeline-kanban
```

Then start a fresh Hermes session or reload skills.

If your Hermes installation supports skill install from URL, you can also install from:

```text
https://raw.githubusercontent.com/perejaslav/nonfiction-book-pipeline-kanban/main/SKILL.md
```

Note: this repository includes supporting files (`scripts/`, `templates/`, `references/`), so cloning the full repository is recommended.

## Natural-language usage

The intended workflow is not terminal-first. The user should be able to say:

```text
Write a 70,000-word popular-science book about the Trebizond Empire. Use Kanban. Find and cross-check sources yourself.
```

or:

```text
Here is my plan and source list. Write the book using Kanban.
```

Hermes should then use this skill as the operator playbook and run the setup internally.

## Manual operator usage

For operators who want to run the initializer directly:

```bash
python3 ~/.hermes/skills/nonfiction-book-pipeline-kanban/scripts/init-project.py \
  "Book Title" ~/my-book \
  --synopsis-file ~/synopsis.md \
  --source-mode agent
```

The script runs a soft preflight that checks required profiles (`researcher`, `analyst`, `writer`, `reviewer`, `default`) and the Kanban runtime. It repairs missing profiles when possible and warns about anything still missing instead of aborting installation.

Source modes:

```bash
--source-mode user   # requires ~/my-book/sources/ or ~/my-book/sources/urls.txt
--source-mode agent  # default: researcher performs web source audit
--source-mode none   # skip separate Source Audit
```

Validate artifacts:

```bash
python3 ~/.hermes/skills/nonfiction-book-pipeline-kanban/scripts/validate-project.py ~/my-book --stage all
```

## Requirements

- Hermes Agent with Kanban support.
- Profiles conventionally named:
  - `researcher`
  - `analyst`
  - `writer`
  - `reviewer`
  - `default`
- A working model/provider configuration for those profiles.
- Gateway or dispatcher runtime for Kanban task execution.

## Routing rule

For new end-to-end book projects where the user explicitly asks to use Kanban, use this skill.

If the user explicitly says not to use Kanban, use the classic `nonfiction-book-pipeline` skill instead.

## Repository contents

```text
SKILL.md                         Main Hermes skill
references/kanban-setup.md       Setup and troubleshooting notes
references/audit-v2-lessons.md   Audit lessons and confidence framing
scripts/init-project.py          Robust initializer
scripts/validate-project.py      Artifact validator
templates/intake-template.json   Intake template
```

## License

MIT
