# Weekly Status Report Instructions

## Input format

Use the user's request and any supplied project notes, backlog, task tracker, or verified report data. Prefer current, dated sources over older notes. Useful inputs include:

- Reporting period or report date
- Completed work and supporting source
- Blockers and their impact
- Planned work for next week
- Relevant data gaps

Inputs may be prose or files in the workspace. Do not request or include credentials, tokens, or other secrets.

## Processing steps

1. Review the relevant available sources and identify facts for accomplishments, blockers, and next-week work.
2. Keep the report limited to the requested team or project and reporting period.
3. Use only facts supported by the inputs. Do not invent dates, progress, metrics, causes, owners, or forecasts.
4. Do not present undated or ongoing status as work completed during the reporting period. If timing is not supported, state that period attribution is unavailable or clearly identify the information as current status.
5. Do not treat project names, reporting dates, or other request metadata as accomplishments; list only verified completed work as accomplishments.
6. If an important fact or source is unavailable, state that briefly under the most relevant section instead of guessing. Distinguish unavailable information from sources that affirmatively report none.
7. Remove duplicate or unrelated details and use concise, professional wording.

## Output format and constraints

- Generate the report in Markdown format.
- Do not use Markdown headings.
- Use only these section labels, each as a top-level bullet:
  - Accomplishments
  - Blockers
  - Next Week
- Place the section content as nested bullets under the matching section label.
- If reviewed sources affirmatively indicate that a section has no items, include a nested bullet stating "None reported." If the relevant information or source is unavailable, say what is unavailable instead; do not imply that no items exist.
- Use bullet points only; do not use prose, tables, or other formatting.
- If the user requests a conflicting format, follow these output constraints and do not add commentary about the conflict inside a report section.
- Keep the report to a maximum of 20 lines.
- Use a professional tone.
- Use clear, direct language.
- Do not use fluff words.
