# Specification Clarifications

This review assesses [constitution.md](constitution.md) and
[specification.md](specification.md) against implementation readiness. Items
marked **Blocking** must be resolved before implementation starts. **High**
items materially affect design or acceptance behavior. **Medium** items need
clarification before or during detailed planning.

## Resolution Status

All items below have been resolved in the specification as explicit prototype
decisions or out-of-scope exclusions.

| Item | Resolution |
|---|---|
| 1. MVP delivery mode | CLI plus standalone HTML; React/Vite UI, Express API, Docker, and PostgreSQL are out of scope. |
| 2. Confluence scope | Out of scope; no Confluence reads or writes. |
| 3. Configuration contract | JSON plus exact environment-variable names; environment variables override matching JSON keys. |
| 4. Authentication and authorization | Jira API token plus account email; prototype is local CLI and has no web authentication. |
| 5. Blocked status | Exact Jira status name, case-insensitive, default `Blocked`; status-ID allowlists are deferred. |
| 6. Database behavior | PostgreSQL and database migrations are out of scope; the last HTML file is retained only. |
| 7. Scheduling | One local-Windows-task run per selected time, local timezone, no overlap; missed-run retry is deferred. |
| 8. Complete Jira response | Board, sprint, status, status category, issue key, summary, and current-sprint fields are mandatory; missing optional assignee/link handling is explicit. |
| 9. Story-point missing values | Invalid, missing, null, negative, or non-finite values make story-point totals unavailable. |
| 10. Story-point percentage | Completed points divided by current total points, rounded to two decimal places for display. |
| 11. Active sprint | Exactly one active sprint required; zero or multiple active sprints are fatal configuration/data errors. |
| 12. Pagination | Retrieve all Jira pages using configured page size and bounded retries; stop on inconsistent, duplicate, or incomplete data. |
| 13. Snapshot time | Refresh start time is the snapshot anchor; all blocker-age calculations use that one timestamp. |
| 14. Completion override | Jira `Done` status category is the prototype rule; status allowlists are deferred. |
| 15. Executive summary | Deterministic template: sprint identity, issue totals, story-point state, and blocker count; no AI narrative. |
| 16. Stale report | Failed refreshes retain the last successful HTML and its timestamp; a report older than 24 hours displays a stale-data warning. |
| 17. HTML response | Standalone UTF-8 HTML file, responsive, direct Jira links, no credentials, and user opens it from disk. |
| 18. API behavior | REST API is out of scope; CLI exit status and stderr errors are the prototype contract. |
| 19. Refresh source | CLI only; no client-supplied source field. Manual versus scheduled behavior is determined by the process entry point. |
| 20. Report path | Configurable Windows output path; atomic write creates a sibling temporary file and replaces the target. |
| 21. Artifact authority | The HTML is the sole report artifact and source of truth for the prototype; no database copy is required. |
| 22. Security | Local CLI and HTTPS Jira API; no web threat surface; credentials come from environment variables and never enter HTML/logs. |
| 23. Status ordering | Status categories use `To Do`, `In Progress`, `Done`, then unknown categories; exact statuses sort alphabetically; zero-count statuses are omitted. |
| 24. Issue ordering | Accomplishments and blockers sort by issue key ascending. |
| 25. Time format | Store timestamps in UTC ISO 8601 and display the report in the local Windows timezone with a timezone label. |
| 26. Numeric precision | Story points allow up to two decimal places; completion percentages display two decimal places; values round with standard decimal half-up rounding. |
| 27. Configuration UI | No configuration UI or configuration API; JSON and environment variables are read-only at each execution. |
| 28. Concurrency | Scheduled and manual runs must not overlap; user or task scheduler is responsible for preventing overlap. |
| 29. Assignee PII | Store only display-name strings in the generated HTML when permitted; no database retention; account IDs are not persisted. |
| 30. Accessibility | HTML uses semantic elements and readable contrast; WCAG 2.1 AA is a target, with no formal audit requirement. |
| 31. Dependencies | Pin Python, package, and Atlassian client versions through repository manifests and lock files. |
| 32. Language and tooling | Python CLI; pytest for tests, repository formatter/linter, and existing package conventions. |
| 33. Existing implementation | Reuse or migrate existing `generate_sprint_report.py` and Jira helper tools only when they satisfy the clarified rules. |

## Blocking

### 1. MVP delivery mode is contradictory

The constitution requires React 18/Vite, Express, PostgreSQL, and Docker. The
source requirements define a local standalone HTML report and explicitly
exclude an interactive web dashboard. The specification then defines HTTP
endpoints and UI screens, but its implementation plan says the React UI is
required only "if required by the approved MVP."

**Decision needed:** Choose one of:

- CLI plus standalone HTML only, with no React/Express UI.
- React/Express application plus standalone HTML preview and download.
- CLI first, with a separately approved web interface phase.

PostgreSQL use must also be decided consistently with the selected mode.

### 2. Confluence scope is unresolved

The project name and constitution describe Jira/Confluence automation,
synchronization, and publication, while the specification defines a Jira-only
MVP and explicitly excludes Confluence integration and writes.

**Decision needed:** Specify whether Confluence is in scope for this release,
and, if it is, define spaces, pages, source mappings, approval, conflict
handling, and API credentials.

### 3. Configuration and secrets have no complete contract

The specification lists required values but not environment-variable names,
JSON/file precedence, validation rules, or the method for discovering Jira
board and story-point fields.

Define the exact:

- Environment variable names
- JSON configuration schema
- Secret store format
- Precedence between environment variables and JSON
- Required versus optional fields
- Board discovery command or rule
- Story-point field discovery rule
- Jira account authentication method

### 4. Authentication and authorization are incomplete

Jira authentication is stated as API token plus account email, but no API
authentication endpoint, session model, user roles, or authorization rules are
specified for the local web UI. It is unclear whether the local application is
single-user or has multiple users.

Define whether:

- The React UI is public only on a local loopback host.
- Multiple users exist.
- The frontend is publicly exposed.
- Login, SSO, OAuth, or OS-local trust is required.
- Scheduled tasks use the same credentials.

### 5. Blocked-status rule is contradictory

FR-010 requires status exactly `Blocked`, while FR-001 makes the blocked status
configurable and the constitution supports status mappings. Both the status
text and exact Jira status ID/name are underdefined.

Define whether blockers use:

- Exact status name.
- Jira status ID.
- Status category.
- A configurable allowlist.

The source specification's default is `Blocked`, but case-insensitive behavior
must also be tested and documented.

### 6. Database behavior is incompletely defined

The specification requires a single `latest_report`, but it does not define
database startup behavior, migrations, uniqueness constraints, connection
settings, transaction boundaries, rollback behavior, or what happens when
PostgreSQL itself is unavailable.

Clarify whether:

- The report can be generated if PostgreSQL is unavailable.
- PostgreSQL stores only latest state or also run history.
- All latest report tables are replaced atomically.
- Failed refreshes create run rows.
- Database retention or purge policy exists.
- Configuration is read from PostgreSQL or environment files.

### 7. Scheduled refresh design is underspecified

The specification requires one refresh per calendar day and a user-selected
local time, but it does not define timezone, missed-run behavior, overlapping
runs, concurrency, startup behavior, or retry behavior.

Define:

- Which local timezone and DST rule are used.
- Whether scheduled and manual refreshes may overlap.
- Whether missed runs are retried at the next startup.
- Whether failure notifications exist.
- How run status is recorded by a headless Windows scheduled task.

### 8. "Complete Jira response" has no completeness definition

The spec uses `503`, `502`, and `422` status codes but never defines Jira fields
that are mandatory for generation, partial-page handling, missing permissions,
or malformed API responses.

Define required fields and validation behavior for:

- Board lookup.
- Active sprint lookup.
- Sprint issue pages.
- Status and status category.
- Story-point field.
- Assignee.
- Issue update time.
- Jira links.

Assignee and issue links may be optional, while sprint dates and status category
may be mandatory. The final list must be explicit.

## High

### 9. Story-point missing-data rules are not precise

The spec says missing values make totals unavailable, but it does not say
whether:

- Missing values on completed issues only affect completed totals.
- Missing values affect remaining totals individually.
- A report can show available issue totals while story points are unavailable.
- Invalid string values, negative values, zero, and decimal values are handled
  consistently.
- Values are rounded and with what precision.
- Negative values are invalid or merely excluded.

### 10. Story-point percentage denominator is unclear

The percentage formula is not explicitly defined in every case. It may be
calculated as completed / total story points, but the spec does not state that
rule, rounding, or how remaining points relate to scope change.

Define scope changes during a sprint and whether the denominator is:

- Initial committed scope.
- Current sprint scope.
- Completed plus remaining points.

### 11. Active-sprint resolution needs a tie-break rule

The spec rejects all multiple active sprint results. Jira may legitimately
require disambiguation by board ID and configured project. It is unclear
whether the board itself can have no active sprint, whether future/closed
states count, and whether several active states can occur in Jira.

Define zero-sprint, one-sprint, and multiple-sprint behavior and the exact
Jira API calls used.

### 12. Issue pagination completeness is underspecified

The spec requires pagination but does not state the Jira API pagination
strategy, page size, maximum number of pages, retry behavior, or how duplicate
or changing issues are handled during a refresh.

Define token or offset pagination, duplicate detection, issue de-duplication,
and refresh behavior if issue data changes between pages.

### 13. Jira data snapshot semantics are missing

The same refresh timestamp is used for data retrieval and blocker age
calculation, but Jira API calls occur over time. It is unclear whether each
issue has a source-specific timestamp or whether refresh start/end time is used.

Define whether the snapshot is anchored to refresh start or completion and how
Jira data changed during retrieval is detected.

### 14. Issue completion definition allows an undefined override

FR-007 and FR-008 say `Done` status category is the default, while FR-004
allows a later configurable allowlist. The MVP acceptance criteria do not define
configuration precedence or whether status-category or status-name completion
is used.

Define one completion rule and whether the allowlist is part of MVP
configuration.

### 15. Executive summary format is not testable

The specification requires a deterministic stakeholder narrative but does not
define exact templates, words, thresholds, or status labels. It is not possible
to distinguish factual correctness from an acceptable natural-language summary.

Provide an exact template or deterministic rules for healthy, at-risk,
blocked, empty-sprint, and data-unavailable states.

### 16. Report age and stale-data behavior conflict

The source requirements say stale data must be clearly labeled, while the
latest report screen says failed refresh preserves the previous report and does
not imply that failed data is current. The stale threshold and warning text are
not defined.

Define:

- The age at which a report is stale.
- Warning text for stale and failed-refresh states.
- Whether scheduled-failure notifications are required.
- Whether stale report HTML remains downloadable.

### 17. Report HTML and React preview behavior are unclear

`GET /api/report/html` may return HTML or an attachment, but there is no
specific status code, media type, filename, or browser preview behavior.

Define response headers, file name, Content-Disposition behavior, download
action, CSP, iframe restrictions, and whether links open Jira externally.

### 18. API endpoint behavior is incomplete

The API does not define:

- Authentication or authorization.
- Request validation.
- Error body schema.
- Pagination or filtering.
- Idempotency.
- Concurrent refresh behavior.
- CORS origins.
- Rate limiting.
- Timeout and status behavior.

In particular, `/api/report/html` has no no-report, stale-report, or
refresh-in-progress behavior.

### 19. `POST /api/report/refresh` source is not trustworthy

A client-supplied `source` field can claim the refresh was scheduled. The API
does not define which component assigns run source or prevent manual claims.

Define whether the API accepts `source` and, if so, allow only a server-enforced
enum. Scheduled refreshes should identify themselves server-side.

### 20. HTML output path and Docker mounts are unspecified

The Windows host path is used in the example, but Docker container paths,
volume mounts, permissions, file ownership, and Windows host behavior are not
defined.

Define a container-to-host report path, working directory, volume mount, atomic
write support, and fallback behavior if the host path is unavailable.

### 21. Database and standalone HTML could disagree

The application may persist metrics while serving independently generated HTML.
The spec does not define which artifact is authoritative or how consistency is
validated.

Define whether:

- Database state is generated first and HTML is derived from it.
- HTML is generated first and then persisted.
- A mismatch is detected and either artifact preserved.

### 22. Security threat model and UI exposure are missing

The constitution mandates security controls but not their implementation
defaults. The spec does not specify HTTPS for the local UI, an API authentication
mechanism, CSRF protection, CSP details, rate limiting, or secret rotation.

For a local-only MVP, document loopback binding and OS-permission expectations.
For a networked UI, document authentication and authorization.

## Medium

### 23. Report status counts have no ordering rule

The spec does not define sort order for statuses or status categories.

Specify alphabetical, Jira rank/order, or fixed status-category order and
whether all zero-count statuses are included.

### 24. Issue list order is not defined

Completed accomplishments and highlighted blockers need deterministic ordering.

Specify sort order, for example issue-key ascending or last-updated ascending.
Define whether Jira rank is used and whether names are localized.

### 25. Time and date formats are inconsistent

The examples use ISO timestamps and `YYYY-MM-DD`, but do not specify:

- Local versus UTC storage.
- Display timezone.
- Jira offset handling.
- DST behavior.
- JSON serialization format.

Define one canonical storage format and one display format.

### 26. Numeric precision is unspecified

The spec defines `NUMERIC` and decimal examples but not:

- Story-point precision.
- Completion percentage precision.
- Rounding mode.
- JSON number formatting.
- Display grouping and decimal separators.

### 27. Configuration status response is too broad

The configuration response can expose board and project metadata, and it
does not define whether that metadata is sensitive or whether it is masked.
It also has no full configuration update endpoint or clear edit workflow.

Define the read-only or editable nature of configuration and which fields may
be returned.

### 28. Concurrency and run retention are missing

No unique constraint is defined for active runs, concurrent refresh policy,
run-history retention, or the maximum number of retained failed runs.

Specify one active refresh per instance and retention/purge behavior.

### 29. Assignee names and PII handling are not complete

The constitution includes PII minimization, while the data model always
includes a nullable assignee name. The spec has no retention period,
anonymization option, or account-ID alternative.

Define whether account IDs or display names are stored, and specify PII
retention and deletion behavior.

### 30. Accessibility targets are not testable

“Accessibility” and “keyboard access” are stated generally but no WCAG level,
automated check, or browser support matrix is given.

Specify conformance target and supported desktop/mobile browsers.

### 31. Docker and dependency versions are incomplete

Only primary versions are pinned. No Express, Vite, React patch/package
versions, PostgreSQL image tag, Node image variant, Docker Compose file
version, or lockfile policy is defined.

The spec should pin resolved package versions and database container
images rather than only major or runtime versions.

### 32. Folder structure is not aligned with implementation language

The constitution provides one directory layout and explicitly references
JavaScript/JSX formatting, while the specification allows TypeScript or
JavaScript. It does not choose a language or test runner.

Select JavaScript or TypeScript and define the framework, formatter, linter,
test runner, and build output conventions.

### 33. Existing repository implementation affects scope

The repository already contains a Python `generate_sprint_report.py` and
Jira helper tools. The specification says Node.js/Express must not be replaced
by Python, but it does not explain whether the existing CLI implementation
must be reused, migrated, wrapped, or replaced.

Define migration or reuse requirements for existing report generation code,
tests, configuration, and scheduled-task utilities.

## Recommended Clarification Sequence

1. Resolve MVP delivery mode: CLI-only, web application, or CLI plus web UI.
2. Resolve Confluence scope and whether any Jira/Confluence writes are allowed.
3. Confirm Jira board, project, story-point field, status, and authentication.
4. Decide whether PostgreSQL is required and what failure behavior applies.
5. Define scheduling, timezone, overlap, and missed-run behavior.
6. Finalize API contracts, UI states, and error schema.
7. Resolve calculation, rounding, ordering, and missing-data rules.
8. Choose language, framework versions, package managers, and existing-code
   migration strategy.
