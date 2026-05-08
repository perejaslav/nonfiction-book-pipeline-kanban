#!/usr/bin/env python3
"""Validate artifacts produced by NonFiction-Book-Pipeline-Kanban."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BAD_PATTERNS = [
    r"ВСТАВИТЬ",
    r"PLACEHOLDER",
    r"TODO",
    r"ПРОБЛЕМА ДЛЯ РЕДАКТОРА",
    r"\[уточнить\]",
]


def words(text: str) -> int:
    return len(re.findall(r"\w+", text, flags=re.UNICODE))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--stage", choices=["foundation", "chapters", "manuscript", "all"], default="all")
    ap.add_argument("--min-chapter-words", type=int, default=1000)
    ap.add_argument("--min-chapters", type=int, default=17)
    args = ap.parse_args()

    project = Path(args.project).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []

    intake_path = project / "intake.json"
    if not intake_path.exists():
        errors.append(f"missing intake.json: {intake_path}")
        intake = {}
    else:
        try:
            intake = json.loads(intake_path.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"invalid intake.json: {e}")
            intake = {}

    source_mode = intake.get("source_mode", "agent") if isinstance(intake, dict) else "agent"
    if source_mode in {"user", "agent"} and args.stage in ["foundation", "all"]:
        audit = project / "research" / "00-source-audit.md"
        claims = project / "research" / "00-source-claims.tsv"
        if not audit.exists():
            errors.append(f"missing source audit for source_mode={source_mode}: {audit}")
        if not claims.exists():
            warnings.append(f"missing source claims table for source_mode={source_mode}: {claims}")

    if args.stage in ["foundation", "all"]:
        required = [
            "01-structure.md", "02-facts.md", "03-voice.md", "04-terms.md", "05-chapter-briefs.md"
        ]
        for name in required:
            p = project / "foundation" / name
            if not p.exists():
                errors.append(f"missing foundation file: {p}")
            elif words(p.read_text(encoding="utf-8", errors="ignore")) < 100:
                errors.append(f"too short foundation file: {p}")

    if args.stage in ["chapters", "all"]:
        chapters = sorted((project / "chapters").glob("*.md"))
        if len(chapters) < args.min_chapters:
            errors.append(f"too few chapter files: {len(chapters)} < {args.min_chapters}")
        for ch in chapters:
            text = ch.read_text(encoding="utf-8", errors="ignore")
            wc = words(text)
            if wc < args.min_chapter_words:
                warnings.append(f"short chapter: {ch.name} = {wc} words")
            for pat in BAD_PATTERNS:
                if re.search(pat, text, flags=re.I):
                    errors.append(f"bad pattern {pat!r} in {ch}")

    if args.stage in ["manuscript", "all"]:
        manuscript = project / "manuscript.md"
        if not manuscript.exists():
            errors.append(f"missing manuscript: {manuscript}")
        else:
            text = manuscript.read_text(encoding="utf-8", errors="ignore")
            wc = words(text)
            target = int(intake.get("target_words") or 0)
            if target and not (target * 0.8 <= wc <= target * 1.2):
                warnings.append(f"word count outside ±20%: {wc} vs target {target}")
            if not text.startswith("---\n"):
                errors.append("manuscript missing YAML frontmatter")
            for pat in BAD_PATTERNS:
                if re.search(pat, text, flags=re.I):
                    errors.append(f"bad pattern {pat!r} in manuscript")

    report_dir = project / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / f"validation-{args.stage}.md"
    report.write_text(
        "# Validation report\n\n"
        f"Project: `{project}`\n\n"
        f"Errors: {len(errors)}\n\n"
        + "\n".join(f"- ERROR: {e}" for e in errors)
        + "\n\n"
        f"Warnings: {len(warnings)}\n\n"
        + "\n".join(f"- WARNING: {w}" for w in warnings)
        + "\n",
        encoding="utf-8",
    )

    print(report)
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(" -", w)
    if errors:
        print("ERRORS:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
