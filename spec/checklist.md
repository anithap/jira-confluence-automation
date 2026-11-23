# Specification Implementation Checklist

**Specification:** [specification.md](specification.md)
**Constitution:** [constitution.md](constitution.md)
**Test baseline:** `python -m unittest discover -s tests -v`
**Test result:** 28 tests passed

Status meanings:

- **Implemented / works:** Source code exists and available fixture/unit tests
  verify the behavior.
- **Implemented / partially works:** Most behavior exists, but configuration,
  live integration, or a required edge case remains unverified.
- **Implemented / not runtime-verified:** Code or configuration exists, but the
  required external service could not be exercised.
- **Missing:** No implementation found.
- **Out of scope:** The specification or current prototype intentionally
  excludes it.

## Current scope note

The repository currently contains a working Python CLI report implementation.
It does not contain the React/Express/PostgreSQL web application described by
the later web-plan documents. Checklist results therefore use the
clarified specification's Python/HTML prototype scope where it conflicts with
the web replacement plan.

## Functional Requirements

| ID | Requirement | Implemented | Does it work? | Evidence |
|---|---|---|---|---|
| FR-001 | Load and validate JSON/environment configuration | Implemented, partially | Partially | `load_config()` validates legacy snake-case JSON keys. The clarified camel-case keys and exact environment override contract are not implemented. |
| FR-002 | Authenticate to Jira Cloud | Implemented | Not live-verified | HTTP Basic credentials are created in `JiraClient`; unit tests do not contact Jira. |
| FR-003 | Resolve exactly one active sprint | Implemented | Fixture-verified | Existing tests cover a one-sprint fixture. Zero/multiple-sprint CLI behavior is implemented; live Jira behavior is unverified. |
| FR-004 | Retrieve and normalize paginated sprint issues | Implemented, partially | Partially | Pagination exists and continues across pages. Required-field completeness and duplicate/inconsistent snapshot checks are incomplete. |
| FR-005 | Generate deterministic executive summary | Implemented | Fixture-verified | HTML summary is generated from calculated metrics, but not the clarified exact template. |
| FR-006 | Show exact status and status-category counts | Implemented | Unit-tested | `summarize_issues()` builds sorted status/count/category rows and HTML renders them. |
| FR-007 | Calculate issue completion using `Done` | Implemented | Unit-tested | Completed, remaining, total, and percentage logic are covered by fixtures. |
| FR-008 | Calculate story-point progress and unavailable values | Implemented | Unit-tested | Missing/null/negative handling and unavailable totals are covered. Decimal rounding and two-decimal rules are not fully specified in code. |
| FR-009 | List completed accomplishments | Implemented | Unit-tested | `done` issues are rendered with key, summary, assignee, status, update time, and link. |
| FR-010 | Highlight old `Blocked` issues | Implemented | Unit-tested | Exactly-five-day and newer/missing-update cases are covered. |
| FR-011 | Render a standalone HTML report | Implemented | Fixture-verified | HTML escaping and report sections are tested. Stale 24-hour warning and local-timezone label are not implemented. |
| FR-012 | Write report atomically and preserve previous output | Implemented | Implemented / not failure-verified | Temporary file plus `os.replace()` exists. No focused injected file-write failure test was found. |
| FR-013 | Support manual and Windows scheduled execution | Implemented, partially | Manual code present; scheduling not runtime-verified | `--config` CLI exists. `install_daily_task.ps1` and README scheduling exist; overlap lock/missed-run behavior are not verified. |
| FR-014 | Prevent Jira writes and external distribution | Implemented | Fixture/inspection verified | Report client contains read-only Jira endpoints. No distribution code was found. |
| FR-015 | Fail safely and preserve report | Implemented, partially | Partially | `main()` catches `ReportError`, writes no report after fetch/render failure, and writes atomic output. Token and config errors are handled. Full injected failure tests are not present. |

## User Stories

| User story | Implemented | Does it work? | Evidence |
|---|---|---|---|
| US-1: Generate sprint report | Implemented | Unit/HTML fixture verified | CLI, Jira retrieval, metrics, and HTML renderer exist. Live Jira credentials and IDs are not configured. |
| US-2: Refresh on schedule | Implemented, partially | Not runtime-verified | Scheduling script exists, but Windows Task Scheduler execution was not run in this environment. |
| US-3: Refresh manually | Implemented | Not live-verified | CLI entry point exists and unit tests pass. |
| US-4: Identify completed work | Implemented | Unit-tested | `Done` status category fixtures pass. |
| US-5: Identify blockers | Implemented | Unit-tested | Five-day and missing-update fixtures pass. |
| US-6: Recover from Jira failure | Implemented, partially | Not failure-verified | Atomic writer and error handling exist, but no end-to-end injected failure test was found. |

## API and UI Scope

| Requirement | Implemented | Does it work? | Evidence |
|---|---|---|---|
| Express REST endpoints | Missing / out of scope for current prototype | N/A | `backend/package.json` is empty and backend source is only placeholders. |
| React/Vite frontend | Missing / out of scope for current prototype | N/A | `frontend/package.json` is empty and source is only a placeholder. |
| Standalone HTML as complete UI | Implemented | Fixture-verified | HTML renderer and unit tests exist. |
| Configuration status UI | Missing / out of scope | N/A | No web UI exists. |
| Refresh progress UI | Missing / out of scope | N/A | No web UI or API exists. |

## Data Model

| Requirement | Implemented | Does it work? | Evidence |
|---|---|---|---|
| PostgreSQL persistence | Missing / out of scope for current prototype | Database service exists, application persistence missing | PostgreSQL Compose service was added, but backend migrations and repositories do not exist. |
| Latest successful report in database | Missing | N/A | No persistence layer or entities exist. |
| Refresh run history | Missing | N/A | No database migrations or refresh-run model exist. |
| In-memory domain types | Implemented, partially | Fixture-verified | Python dictionaries represent report and issue data, but no formal typed/domain models exist. |
| Missing values remain distinguishable from zero | Implemented | Unit-tested | `None` represents unavailable story points; issue completion still uses integer counts. |

## Non-Functional Requirements

| ID | Requirement | Implemented | Does it work? | Evidence |
|---|---|---|---|---|
| NFR-001 | Under-five-minute refresh, pagination, bounded retries | Implemented, partially | Unit pagination verified; live timing not verified | Pagination, 100-page maximum, and three-attempt retries exist. Live elapsed time is unknown. |
| NFR-002 | HTTPS, secrets, escaping, assignee controls | Implemented, partially | Fixture/inspection verified | HTTPS URL validation exists. Assignee inclusion is not tied to the clarified environment/UI contract. HTML escaping is tested. |
| NFR-003 | Complete response, preserve report, no live-credential tests | Implemented, partially | Unit suite passes offline | Existing unit suite does not require Jira credentials and report-write logic exists. Completeness validation is incomplete. |
| NFR-004 | Separate integration, normalization, metrics, rendering | Implemented, partially | Source inspection verified | `JiraClient`, `fetch_sprint_data`, `summarize_issues`, and `render_report` are separate functions, but not in a formal package boundary. |
| NFR-005 | Semantic HTML, responsive layout, unavailable/error states | Implemented, partially | Not browser-verified | HTML has semantic tags and responsive CSS. No browser screenshot or accessibility audit was run. |
| NFR-006 | Windows/Python deployment | Implemented | Manual setup documented | Python CLI and Windows scheduling README exist. Supporting dependencies are not pinned in `requirements.txt`. |

## Configuration Contract

| Requirement | Implemented | Does it work? | Evidence |
|---|---|---|---|
| JSON configuration | Implemented | Unit/inspection verified | Existing `config.example.json` and `load_config()` use it. |
| Camel-case clarified keys | Missing | N/A | The implementation uses snake-case keys. |
| Environment-variable overrides for non-secret settings | Missing | N/A | Only `api_token_env` supports runtime secret lookup; non-secret environment overrides are not implemented. |
| Exact environment variable names | Missing | N/A | The implementation uses `JIRA_API_TOKEN` by default only if configured in JSON. |
| Unknown JSON keys rejection | Missing | N/A | `load_config()` does not reject unknown keys. |
| Secret never stored in JSON | Implemented | Inspection verified | Example JSON does not contain a token; it names a token environment variable. |
| Assignee inclusion setting | Missing | N/A | Assignee names are always included in the Python report. |

## Testing and Quality

| Requirement | Implemented | Does it work? | Evidence |
|---|---|---|---|
| Unit tests do not require live Jira | Implemented | Works | 28 repository unit tests pass offline. |
| Story-point missing-data tests | Implemented | Works | Missing story-point test passes. |
| Exactly-five-day blocker test | Implemented | Works | Boundary test passes. |
| HTML escaping test | Implemented | Works | Script-like Jira summary escaping test passes. |
| Atomic writer test | Missing | N/A | No focused temporary-file/replace/failure test found. |
| PostgreSQL integration tests | Missing | N/A | No backend test setup or database. |
| Docker Compose startup test | Missing | Docker engine unavailable | Compose configuration is valid, but live PostgreSQL startup could not be confirmed. |
| Live Jira integration test | Missing | N/A | No board ID, story-point field, or token was supplied. |
| Scheduled-task runtime test | Missing | N/A | Windows scheduled task was not executed in this check. |

## Out-of-Scope Items

| Item | Status |
|---|---|
| React/Vite UI | Out of scope for current prototype; not implemented |
| Express REST API | Out of scope for current prototype; not implemented |
| PostgreSQL application persistence | Out of scope for current prototype; only infrastructure was added |
| Docker runtime for the Python prototype | Out of scope; Docker PostgreSQL setup is web/full-app infrastructure |
| Confluence reads/writes | Out of scope; not implemented |
| Jira writes | Out of scope; not implemented |
| Email, chat, Jira, or Confluence distribution | Out of scope; not implemented |
| OAuth/multi-user authentication | Out of scope; not implemented |
| Historical snapshots or burnup | Out of scope; not implemented |

## Docker/PostgreSQL Current State

`docker-compose.yml` now contains a PostgreSQL 15 service with a persistent
volume and healthcheck. `.env.example` and `.gitignore` protect local database
configuration.

Runtime verification remains incomplete:

- `docker compose config` succeeds with a local `.env`.
- Docker Engine startup was not confirmed in this environment.
- Database connectivity and migration state are not verifiable until BE-002 and
  BE-003 are implemented.

## Summary

### Implemented and verified

- Offline unit test suite passes.
- Jira sprint metrics and report rendering functions exist.
- Missing story points, `Done` completion, blockers, pagination fixtures, and
  HTML escaping pass focused tests.
- Standalone HTML report generation exists.
- Existing report is preserved by `os.replace()` behavior on successful output,
  and source fetch/render failures exit before writing.

### Implemented but not fully verified

- Live Jira authentication and board/sprint retrieval.
- Manual CLI execution with real configuration.
- Atomic write failure behavior.
- Windows scheduled-task execution.
- Pagination with real Jira data.
- Under-five-minute live performance.
- Stale-report behavior.

### Missing or not aligned

- Clarified camel-case configuration contract and environment overrides.
- Assignee inclusion setting.
- 24-hour stale-report warning.
- Exact deterministic two-decimal story-point and percentage formatting.
- Complete pagination/response completeness validation.
- Concurrency/run lock.
- PostgreSQL migrations and repositories.
- Express API and React UI.
- Supporting dependency lockfile.

## Recommended Next Actions

1. Resolve the prototype-versus-web scope contradiction.
2. Complete the clarified camel-case configuration contract or intentionally
   retain the legacy contract.
3. Add a stale-report warning and exact numeric formatting.
4. Add migration tooling and database entities for the web application phase.
5. Add injected failure tests for Jira and report writes.
6. Verify Docker and PostgreSQL after the Docker engine is running.
7. Perform one live read-only Jira smoke test with a confirmed board and
   story-point field.

## Gap Disposition

### Real gaps to implement now

These gaps affect the existing Python/HTML prototype and can be resolved
without adding Express, React, or PostgreSQL application persistence:

1. **Clarified configuration contract**
   - Add camel-case JSON keys and exact environment-variable overrides.
   - Reject unknown JSON keys.
   - Preserve legacy snake-case keys only as a documented compatibility layer.
2. **Assignee inclusion setting**
   - Honor `includeAssigneeNames` / `INCLUDE_ASSIGNEE_NAMES`.
   - Omit assignee data or label it consistently when disabled.
3. **Stale-report warning**
   - Display a warning when the report is more than 24 hours old.
   - Preserve the original UTC refresh timestamp.
4. **Numeric formatting**
   - Display percentages to two decimal places.
   - Apply decimal half-up rounding to story-point display values.
5. **Response validation and run concurrency**
   - Reject duplicate issue keys and inconsistent project/sprint data.
   - Implement a local process run lock if it can be tested reliably.
6. **Atomic-write failure coverage**
   - Inject temporary-file or replacement failures.
   - Verify the existing report remains unchanged.

These items are implementation work for the current prototype.

### Clearly out of scope

These items must not block prototype completion:

- React/Vite application screens
- Express REST endpoints
- PostgreSQL application persistence and migrations
- Docker runtime for the Python prototype
- Confluence reads or writes
- Jira issue or sprint mutations
- Email, chat, Jira, or Confluence distribution
- OAuth and multi-user authentication
- Historical report snapshots
- Story-point burnup or burndown charts
- Public hosting or external network access

The PostgreSQL Docker service is infrastructure for a future web phase, not an
implemented prototype feature.

### Nice-to-have polish

- Browser screenshot or accessibility audit
- Formal Python dependency lockfile
- Additional HTML visual styling and status-color conventions
- Additional Windows scheduled-task diagnostics
- Live Jira smoke-test automation
- Refresh-duration and Jira-request observability
- More detailed CLI success output
- Additional status-count ordering options
- Documentation examples for valid test configuration

## Disposition Summary

- **Implement now:** configuration compatibility, assignee control,
  stale-report warning, numeric formatting, response validation/concurrency,
  and atomic-write failure coverage.
- **Out of scope:** web UI/API, database persistence, Confluence, Jira writes,
  distribution, OAuth, historical snapshots, and burnup charts.
- **Nice to have:** browser/accessibility review, dependency pinning,
  diagnostics, live smoke automation, observability, and presentation polish.
