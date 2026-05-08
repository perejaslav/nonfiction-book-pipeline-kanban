#!/usr/bin/env python3
"""
Robust initializer for NonFiction-Book-Pipeline-Kanban.

Creates:
- project directory structure
- intake.json template (unless --synopsis-file is provided)
- Kanban board
- 10-11 dependency-gated tasks via official Hermes CLI, not raw SQLite
- optional Source Audit mode: user | agent | none

Usage:
  python3 init-project.py "Book Title" ~/my-book [--synopsis-file synopsis.md]

After editing intake.json:
  HERMES_KANBAN_BOARD=my-book hermes kanban dispatch --dry-run
  hermes gateway run   # gateway contains the dispatcher by default in current Hermes
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
REQUIRED_PROFILES = ["researcher", "analyst", "writer", "reviewer", "default"]


def sh(args: list[str], *, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    r = subprocess.run(args, text=True, capture_output=True, env=merged)
    if check and r.returncode != 0:
        print("FAILED:", " ".join(args), file=sys.stderr)
        print(r.stdout, file=sys.stderr)
        print(r.stderr, file=sys.stderr)
        sys.exit(r.returncode)
    return r


def slugify(path_or_title: str) -> str:
    raw = Path(path_or_title).name.lower().strip()
    raw = re.sub(r"[^a-z0-9а-яё_-]+", "-", raw, flags=re.I)
    raw = re.sub(r"-+", "-", raw).strip("-")
    return raw or "nonfiction-book"


def ensure_project(project: Path, title: str, synopsis_file: Path | None, source_mode: str) -> None:
    for d in [
        "foundation",
        "research",
        "sources",
        "chapters",
        "drafts",
        "assets/images",
        "assets/tables",
        "assets/maps",
        "scripts",
        "templates",
        "reports",
        "checkpoints",
    ]:
        (project / d).mkdir(parents=True, exist_ok=True)

    intake = project / "intake.json"
    if synopsis_file:
        synopsis = synopsis_file.expanduser().read_text(encoding="utf-8")
    elif intake.exists():
        return
    else:
        synopsis = "ВСТАВИТЬ СИНОПСИС — НЕ ЗАПУСКАТЬ PIPELINE, ПОКА ЭТОТ ТЕКСТ НЕ ЗАМЕНЁН."

    data = {
        "title": title,
        "subtitle": "",
        "author": "",
        "synopsis": synopsis,
        "language": "ru",
        "target_words": 70000,
        "target_chapters": 16,
        "tone": "академический научно-популярный",
        "source_mode": source_mode,
        "source_policy": {
            "user": "Use project/sources/ files and project/sources/urls.txt as primary evidence; do not ignore them.",
            "agent": "Researcher must perform web research and cross-check claims independently.",
            "none": "Skip separate Source Audit; still perform basic research and caution on uncertain claims."
        }.get(source_mode, "agent"),
        "quality_bar": {
            "min_chapter_words": 1500,
            "target_chapter_words": 2500,
            "require_cautious_claims": True,
            "forbid_placeholders": True,
            "require_source_register": source_mode != "none",
        },
    }
    intake.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def validate_sources(project: Path, source_mode: str) -> None:
    sources = project / "sources"
    if source_mode == "user":
        files = [p for p in sources.rglob("*") if p.is_file()] if sources.exists() else []
        urls = sources / "urls.txt"
        has_urls = urls.exists() and urls.read_text(encoding="utf-8", errors="ignore").strip()
        if not files and not has_urls:
            sys.exit(f"ERROR: --source-mode user requires files in {sources}/ or {urls}")
    elif source_mode == "agent":
        sources.mkdir(parents=True, exist_ok=True)
        note = sources / "README-agent-mode.md"
        if not note.exists():
            note.write_text("Source mode: agent. Researcher must find and cross-check sources via web search.\n", encoding="utf-8")


def validate_intake(project: Path, allow_placeholder: bool) -> None:
    intake = project / "intake.json"
    if not intake.exists():
        sys.exit(f"ERROR: missing {intake}")
    data = json.loads(intake.read_text(encoding="utf-8"))
    required = ["title", "synopsis", "language", "target_words", "target_chapters", "tone"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        sys.exit(f"ERROR: intake.json missing fields: {missing}")
    if not allow_placeholder and "ВСТАВИТЬ СИНОПСИС" in data.get("synopsis", ""):
        sys.exit("ERROR: intake.json still contains placeholder synopsis. Edit it or pass --allow-placeholder for setup-only.")


def ensure_profiles() -> None:
    existing = sh(["hermes", "profile", "list"], check=False).stdout
    for profile in REQUIRED_PROFILES:
        if profile not in existing:
            # clone active profile so config/model/env are inherited
            sh(["hermes", "profile", "create", profile, "--clone"], check=False)
        shown = sh(["hermes", "profile", "show", profile], check=False).stdout
        if "model" not in shown.lower():
            print(f"WARNING: profile '{profile}' may not have a model. Check: hermes profile show {profile}", file=sys.stderr)


def ensure_board(board: str) -> None:
    boards = sh(["hermes", "kanban", "boards", "list"], check=False).stdout
    if board not in boards:
        sh(["hermes", "kanban", "boards", "create", board])


def create_task(board: str, title: str, assignee: str, body: str, parents: list[str] | None = None,
                priority: int = 0, skill: str | None = None, max_runtime: str = "2h") -> str:
    args = [
        "hermes", "kanban", "create", title,
        "--assignee", assignee,
        "--body", body,
        "--workspace", "scratch",
        "--priority", str(priority),
        "--idempotency-key", f"nfp-kanban:{board}:{slugify(title)}",
        "--max-runtime", max_runtime,
        "--json",
    ]
    for p in parents or []:
        args.extend(["--parent", p])
    if skill:
        args.extend(["--skill", skill])
    r = sh(args, env={"HERMES_KANBAN_BOARD": board})
    try:
        data: dict[str, Any] = json.loads(r.stdout)
    except Exception:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)
        raise
    return data["id"]


def task_bodies(project: Path, source_mode: str) -> dict[str, str]:
    p = str(project)
    if source_mode == "user":
        source_audit = f"""SOURCE AUDIT MODE: USER PROVIDED SOURCES.
Прочитать {p}/intake.json, все файлы в {p}/sources/ и {p}/sources/urls.txt если существует.
Задача: составить проверяемый источнико-ориентированный реестр.
Выходы:
- {p}/research/00-source-audit.md — список источников, что из них можно использовать, ограничения, противоречия.
- {p}/research/00-source-claims.tsv — claim | source | confidence | notes.
Правила: источники пользователя имеют приоритет; если источник сомнителен — сказать прямо; не выдумывать библиографические данные."""
    elif source_mode == "agent":
        source_audit = f"""SOURCE AUDIT MODE: AGENT WEB RESEARCH.
Пользователь не дал источники и передал поиск агенту. Прочитать {p}/intake.json и самостоятельно найти информацию в интернете.
Задача: не просто собрать факты, а перепроверить ключевые claims минимум по 2 независимым источникам, где возможно.
Выходы:
- {p}/research/00-source-audit.md — найденные источники с URL/названиями, оценка надёжности, противоречия.
- {p}/research/00-source-claims.tsv — claim | source(s) | confidence | notes.
Правила: не использовать непроверенные сайты как единственную основу для важных утверждений; спорные claims маркировать как uncertain."""
    else:
        source_audit = ""
    return {
        "source_audit": source_audit,
        "research": f"""Прочитать {p}/intake.json и, если существует, {p}/research/00-source-audit.md. Составить исследовательское досье для книги.
Выходы:
- {p}/research/01-source-map.md — карта источников и тем
- {p}/research/02-factual-spine.md — фактический каркас: даты, имена, события, спорные места
- {p}/research/03-risk-register.md — где высок риск галлюцинаций/спорных утверждений
Требование: помечать сомнительные места словами вероятности, не выдумывать источники.""",
        "foundation": f"""Прочитать {p}/intake.json и {p}/research/*.md.
Создать {p}/foundation/:
01-structure.md — оглавление с номерами глав и краткими задачами каждой главы.
02-facts.md — проверяемые факты, даты, имена, красные флажки.
03-voice.md — стиль: научно-популярный, русский, осторожные формулировки, без гипербол.
04-terms.md — терминологический словарь.
05-chapter-briefs.md — отдельный brief для каждой главы: тезис, сцены/сюжеты, обязательные факты, чего избегать.""",
        "wave1": f"""Написать главы 01–05 в {p}/chapters/ строго по {p}/foundation/05-chapter-briefs.md.
Каждый файл: ## заголовок, 1500–3000 слов, без placeholders, без английских хвостов.
Если brief неясен — не выдумывать, а явно отметить в конце файла 'ПРОБЛЕМА ДЛЯ РЕДАКТОРА'.""",
        "wave2": f"""Написать главы 06–10 в {p}/chapters/ строго по {p}/foundation/05-chapter-briefs.md.
Каждый файл: 1500–3000 слов, единая терминология из 04-terms.md, осторожные фактические claims.""",
        "wave3": f"""Написать главы 11–14 в {p}/chapters/ строго по {p}/foundation/05-chapter-briefs.md.
Каждый файл: 1500–3000 слов, без placeholders, без внутренних противоречий с главами 01–10.""",
        "wave4": f"""Написать главы 15–17, включая заключение, в {p}/chapters/ строго по {p}/foundation/05-chapter-briefs.md.
Заключение должно синтезировать книгу, а не повторять оглавление.""",
        "expansion": f"""Прочитать {p}/chapters/*.md и {p}/foundation/*.md.
Создать справочный аппарат:
18-хронология.md — таблица дат.
19-глоссарий.md — термины.
20-библиография.md — библиография/рекомендуемое чтение; НЕ выдумывать точные издания без уверенности.
21-династия.md — список династии/персоналий, если применимо; если не применимо — заменить на '21-персоналии.md'.""",
        "qa": f"""Проверить артефакты перед сборкой:
- существует {p}/foundation/01-structure.md ... 05-chapter-briefs.md
- существует минимум 17 файлов глав
- нет строки 'ВСТАВИТЬ', 'TODO', 'PLACEHOLDER', 'ПРОБЛЕМА ДЛЯ РЕДАКТОРА'
- главы не пустые, минимум 1000 слов каждая
Записать отчёт в {p}/reports/pre-assembly-qa.md.
Если есть критические проблемы — заблокировать задачу, не пропускать дальше.""",
        "assembly": f"""Собрать {p}/manuscript.md детерминированно из {p}/chapters/*.md в порядке числового префикса.
Перед записью создать backup, если manuscript.md уже существует: {p}/checkpoints/manuscript-before-assembly.md.
Добавить YAML frontmatter из intake.json.
Разделитель между главами: \\newpage.
После сборки записать отчёт word count в {p}/reports/assembly-report.md.""",
        "review": f"""Перед правками скопировать {p}/manuscript.md в {p}/checkpoints/manuscript-before-final-edit.md.
Прочитать manuscript.md целиком. Исправить только реальные проблемы:
1. фактические несостыковки;
2. терминологию;
3. резкие стилистические выбросы;
4. placeholders/оборванные фразы;
5. явные повторы.
Записать отчёт в {p}/reports/final-edit-report.md.""",
        "finalqa": f"""Финальная машинная проверка {p}/manuscript.md.
Проверить: файл существует, word count в целевом диапазоне intake.target_words ±20%, нет placeholders/TODO, все главы присутствуют, frontmatter валиден.
Записать {p}/reports/final-qa.md. Если всё хорошо — завершить с кратким итогом; если нет — заблокировать задачу.""",
    }


def create_graph(board: str, project: Path, source_mode: str) -> None:
    b = task_bodies(project, source_mode)
    research_parents: list[str] = []
    if source_mode in {"user", "agent"}:
        source_audit = create_task(board, f"Source Audit ({source_mode}): evidence register", "researcher", b["source_audit"], priority=110, skill="nonfiction-book-pipeline-kanban", max_runtime="2h")
        research_parents = [source_audit]
    research = create_task(board, "Research: source map and factual spine", "researcher", b["research"], research_parents, priority=100, skill="nonfiction-book-pipeline-kanban")
    foundation = create_task(board, "Foundation: structure facts voice terms briefs", "analyst", b["foundation"], [research], priority=90, skill="nonfiction-book-pipeline-kanban")
    waves = [
        create_task(board, "Wave 1: chapters 01-05", "writer", b["wave1"], [foundation], priority=80, skill="nonfiction-book-pipeline-kanban", max_runtime="3h"),
        create_task(board, "Wave 2: chapters 06-10", "writer", b["wave2"], [foundation], priority=80, skill="nonfiction-book-pipeline-kanban", max_runtime="3h"),
        create_task(board, "Wave 3: chapters 11-14", "writer", b["wave3"], [foundation], priority=80, skill="nonfiction-book-pipeline-kanban", max_runtime="3h"),
        create_task(board, "Wave 4: chapters 15-17 conclusion", "writer", b["wave4"], [foundation], priority=80, skill="nonfiction-book-pipeline-kanban", max_runtime="3h"),
    ]
    expansion = create_task(board, "Expansion: chronology glossary bibliography", "writer", b["expansion"], waves, priority=70, skill="nonfiction-book-pipeline-kanban")
    qa = create_task(board, "QA: pre-assembly artifact validation", "reviewer", b["qa"], [expansion], priority=60, skill="nonfiction-book-pipeline-kanban")
    assembly = create_task(board, "Assembly: deterministic manuscript build", "default", b["assembly"], [qa], priority=50, skill="nonfiction-book-pipeline-kanban")
    review = create_task(board, "Final Edit: manuscript review with backup", "reviewer", b["review"], [assembly], priority=40, skill="nonfiction-book-pipeline-kanban", max_runtime="4h")
    create_task(board, "Final QA: completion report", "reviewer", b["finalqa"], [review], priority=30, skill="nonfiction-book-pipeline-kanban")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("project")
    ap.add_argument("--board", default=None)
    ap.add_argument("--synopsis-file", default=None)
    ap.add_argument("--allow-placeholder", action="store_true", help="allow setup before synopsis is filled")
    ap.add_argument("--source-mode", choices=["user", "agent", "none"], default="agent",
                    help="user: use project/sources or urls.txt; agent: researcher finds/cross-checks web sources; none: skip Source Audit")
    ap.add_argument("--skip-profiles", action="store_true")
    args = ap.parse_args()

    project = Path(args.project).expanduser().resolve()
    board = args.board or slugify(project.name)
    synopsis_file = Path(args.synopsis_file).expanduser() if args.synopsis_file else None

    print(f"Project: {project}")
    print(f"Board:   {board}")
    print(f"Source:  {args.source_mode}")

    ensure_project(project, args.title, synopsis_file, args.source_mode)
    validate_sources(project, args.source_mode)
    validate_intake(project, args.allow_placeholder or synopsis_file is None)
    if not args.skip_profiles:
        ensure_profiles()
    ensure_board(board)
    create_graph(board, project, args.source_mode)

    print("\nREADY")
    print(f"Project: {project}")
    print(f"Board:   {board}")
    print("\nIf intake.json still has a placeholder, edit it before dispatching:")
    print(f"  nano {project / 'intake.json'}")
    print("\nValidate dispatcher view:")
    print(f"  HERMES_KANBAN_BOARD={board} hermes kanban list")
    print(f"  HERMES_KANBAN_BOARD={board} hermes kanban dispatch --dry-run")
    print("\nStart runtime (current Hermes: dispatcher runs in gateway by default):")
    print("  hermes gateway run")


if __name__ == "__main__":
    main()
