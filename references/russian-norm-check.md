# Russian Norm Check

Use this as the strict late-stage Russian-language quality gate for nonfiction manuscripts.

## When to run

Run after the content is already structurally stable and after broad cleanup passes have finished, but before final publication or delivery.

Typical position in the pipeline:

- after Final Edit
- before Final QA / release

## Goal

Verify that the manuscript conforms to clear literary and editorial norms of Russian.

This is not a full academic proofread and not a style rewrite. It is a focused norm check with explicit examples, so the reviewer can catch the class of errors that are easy to miss when many subagents write different chapters.

## Checklist

### 1. Spelling
- obvious spelling errors
- inconsistent spelling of the same term
- mixed Russian / transliterated forms for the same entity
- inconsistent capitalization in proper names and titles

### 2. Punctuation
- comma placement in long subordinate clauses
- colon / semicolon usage in lists and explanations
- parenthetical phrases and dashes
- consistency of commas around participial and adverbial phrases

### 3. Quotation marks
- Russian quotation marks are used consistently: « »
- nested quotes follow a consistent style
- direct quotes are not mixed with paraphrase without markers
- quotation punctuation is stable across chapters

### 4. Dashes and hyphenation
- em dash vs hyphen vs minus are not mixed randomly
- ranges use the correct dash style
- compound terms use consistent hyphenation
- sentence-level dashes follow one house style

### 5. Abbreviations and acronyms
- consistent handling of common abbreviations
- no broken abbreviations at line or section boundaries
- acronyms expand or remain stable according to voice.md / terms.md
- initials and title abbreviations are formatted consistently

### 6. Dates and numbers
- date ranges use one pattern across the book
- BCE/CE style, era markers, and century formatting are consistent
- numbers are written in one house style: digits vs words where applicable
- approximate numbers and ranges are marked consistently

### 7. Transliteration
- the same foreign name is transliterated the same way throughout
- Greek / Latin / Arabic / Turkic names are not mixed in competing spellings
- place names and historical figures match the glossary and facts files

### 8. Terminology consistency
- the same concept uses the same Russian term across chapters
- glossary / terms.md agreement is preserved
- no accidental synonyms where the book requires one fixed term
- titles, offices, dynasties, and technical terms remain stable

## Output

Write a short report to:

```text
reports/russian-norm-check.md
```

The report should include:

- short verdict
- major issues found
- examples with file/chapter references
- whether the manuscript is ready for Final QA

## Recommended workflow

1. Read the full manuscript or the newly edited chapters.
2. Scan for the checklist items above.
3. Note concrete examples instead of generic complaints.
4. Patch only the clearly wrong items.
5. Re-read the patched sections.
6. Write the report.

## Non-goals

- Do not rewrite the whole manuscript.
- Do not perform structural editing.
- Do not re-run fact-check unless a language issue reveals a factual conflict.
- Do not change the authorial voice unless the language error is part of the problem.
