# NonFiction Book Pipeline Kanban

Hermes Agent skill для написания длинных научно-популярных книг через устойчивую Kanban-оркестрацию.

Главная идея: пользователь говорит обычными словами, что за книгу хочет написать, даёт синопсис/план/источники, а Hermes сам делает техническую работу: создаёт проект, Kanban-доску, dependency graph, карточки для researcher/analyst/writer/reviewer, запускает Source Audit, волны написания, QA, сборку manuscript, финальное ревью и валидацию.

## Что умеет

- Создаёт структуру проекта книги.
- Создаёт Hermes Kanban-доску и dependency-gated task graph.
- Поддерживает опциональный Source Audit:
  - `user` — использовать файлы в `sources/` или URL в `sources/urls.txt`.
  - `agent` — researcher сам ищет и перепроверяет источники в интернете. Режим по умолчанию.
  - `none` — пропустить отдельный Source Audit для лёгкого черновика.
- Использует официальный Hermes Kanban CLI: `HERMES_KANBAN_BOARD`, `--json`, `--parent`, `--idempotency-key`.
- Не использует прямые SQLite insert в штатном режиме.
- Добавляет QA-gates перед сборкой и финальной сдачей.
- Включает validator для проверки артефактов, placeholders, количества глав, source-audit outputs и word count.

## Граф pipeline

```text
Source Audit (опционально: user|agent)
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

## Установка

Рекомендуемый способ — клонировать весь репозиторий в директорию skills:

```bash
mkdir -p ~/.hermes/skills/nonfiction-book-pipeline-kanban
git clone https://github.com/perejaslav/nonfiction-book-pipeline-kanban.git \
  ~/.hermes/skills/nonfiction-book-pipeline-kanban
```

После этого начните новую Hermes-сессию или перезагрузите skills.

Если ваша версия Hermes поддерживает установку по URL, можно использовать:

```text
https://raw.githubusercontent.com/perejaslav/nonfiction-book-pipeline-kanban/main/SKILL.md
```

Но лучше клонировать весь репозиторий, потому что скилл использует `scripts/`, `templates/` и `references/`.

## Использование обычным языком

Это не terminal-first workflow. Пользователь должен иметь возможность сказать:

```text
Напиши научно-популярную книгу о Трапезундской империи на 70 000 слов. Используй Kanban. Источники найди и перепроверь сам.
```

или:

```text
Вот мой план и список источников. Напиши по ним книгу через Kanban.
```

Hermes должен сам загрузить этот skill и выполнить техническую работу как оператор.

## Ручной запуск для оператора

Если нужно запустить инициализацию вручную:

```bash
python3 ~/.hermes/skills/nonfiction-book-pipeline-kanban/scripts/init-project.py \
  "Название книги" ~/my-book \
  --synopsis-file ~/synopsis.md \
  --source-mode agent
```

Режимы источников:

```bash
--source-mode user   # требует ~/my-book/sources/ или ~/my-book/sources/urls.txt
--source-mode agent  # default: researcher делает web source audit
--source-mode none   # пропустить отдельный Source Audit
```

Валидация проекта:

```bash
python3 ~/.hermes/skills/nonfiction-book-pipeline-kanban/scripts/validate-project.py ~/my-book --stage all
```

## Требования

- Hermes Agent с поддержкой Kanban.
- Профили:
  - `researcher`
  - `analyst`
  - `writer`
  - `reviewer`
  - `default`
- Рабочая model/provider конфигурация для этих профилей.
- Gateway или dispatcher runtime для выполнения Kanban-задач.

## Правило маршрутизации

Если пользователь явно просит использовать Kanban для новой книги — использовать этот skill.

Если пользователь явно говорит “без Kanban” — использовать classic `nonfiction-book-pipeline`.

## Состав репозитория

```text
SKILL.md                         основной Hermes skill
references/kanban-setup.md       setup и troubleshooting
references/audit-v2-lessons.md   lessons и confidence framing
scripts/init-project.py          robust initializer
scripts/validate-project.py      artifact validator
templates/intake-template.json   intake template
```

## Лицензия

MIT
