# Implementation Tasks

**Plan:** [plan.md](plan.md)
**Specification:** [specification.md](specification.md)
**Constitution:** [constitution.md](constitution.md)
**Status:** Ready for execution

## Task Conventions

- Tasks follow the sequence in [plan.md](plan.md).
- Each task has an imperative title, a `Description`-equivalent Work section,
  testable acceptance criteria, and explicit dependencies.
- A task is complete only when every acceptance criterion passes.
- Dependencies must be completed before implementation begins.
- Test cases must use fixtures or mocks unless a task explicitly requires a live
  Jira smoke test.
- No task may add Jira writes, Confluence writes, external distribution,
  scheduled report delivery, or OAuth.

## Phase 1: Backend Setup

### BE-001: Add PostgreSQL Docker service

**Depends on:** None

**Work:**

1. Configure a PostgreSQL 15 service in `docker-compose.yml`.
2. Define database name, user, password, port, and persistent volume variables.
3. Keep secrets out of source control and Compose defaults.
4. Add a PostgreSQL health check.

**Acceptance criteria:**

- `docker compose up postgres` starts PostgreSQL 15.
- The configured database is reachable only with valid credentials.
- Database data persists across container recreation.
- Docker Compose output and logs contain no database password.

### BE-002: Add migration tooling

**Depends on:** BE-001

**Work:**

1. Add a migration runner to the backend.
2. Add versioned migration files and migration commands.
3. Define migration startup behavior for development and production.
4. Ensure migrations do not log secrets.

**Acceptance criteria:**

- A clean database migrates without manual SQL.
- Re-running migrations is safe.
- Migration status is visible through CLI or backend logs.
- A migration failure stops startup and reports the migration operation.

### BE-003: Create database entities

**Depends on:** BE-002

**Work:**

1. Add migrations for `application_config`, `refresh_run`, `latest_report`,
   `latest_status_count`, and `latest_report_issue`.
2. Add primary keys, foreign keys, indexes, and uniqueness constraints.
3. Add timestamps and nullable fields exactly where unavailable data is
   representable.
4. Ensure at most one current latest report row can exist.

**Acceptance criteria:**

- All entities and relationships create successfully.
- Foreign-key references reject invalid data.
- Multiple latest-report rows cannot be inserted if the uniqueness policy
  disallows them.
- Snapshot, status-count, and issue replacement can run in one transaction.

### BE-004: Create backend application skeleton

**Depends on:** BE-001

**Work:**

1. Initialize the Node.js v26.13.1 and Express application.
2. Load environment variables and validate startup configuration.
3. Add JSON parsing, centralized error handling, request IDs, and HTTP security
   middleware.
4. Configure CORS for approved origins.
5. Add service, controller, route, repository, integration, and middleware
   folders according to the constitution.

**Acceptance criteria:**

- The backend starts in Docker and handles JSON requests.
- Invalid startup configuration produces an actionable error.
- Centralized errors use one redacted response shape.
- Request IDs and credential-safe logs are present.
- CORS and HTTP security headers are enabled.

### BE-005: Implement repository interfaces

**Depends on:** BE-003, BE-004

**Work:**

1. Create repositories for configuration, refresh runs, latest reports, status
   counts, and report issues.
2. Isolate SQL in repository modules.
3. Add transaction support for atomic report replacement.
4. Add bounded run-history or latest-state behavior according to the data
   contract.

**Acceptance criteria:**

- Repositories are exercised with PostgreSQL integration tests.
- Successful report replacement changes all child rows atomically.
- A failed refresh does not modify the latest successful report.
- SQL errors do not expose database credentials or secret values.

### BE-006: Implement API health and configuration routes

**Depends on:** BE-004, BE-005

**Work:**

1. Implement `GET /health`.
2. Implement `GET /api/configuration/status`.
3. Return only non-secret configuration values.
4. Define `500` and `503` responses for unavailable database or configuration.

**Acceptance criteria:**

- Health reports backend and database readiness.
- Configuration status reports validation and masked secret presence.
- Jira token value is never returned.
- Database and secret failures return operation-specific redacted errors.

### BE-007: Implement API report skeleton

**Depends on:** BE-004, BE-005

**Work:**

1. Implement route handlers for report retrieval and run retrieval.
2. Implement `POST /api/report/refresh`.
3. Implement `GET /api/report/html`.
4. Define request/response schemas and consistent error bodies.
5. Prevent concurrent refreshes.

**Acceptance criteria:**

- Every route has success and redacted failure responses.
- Concurrent refresh requests are rejected or coalesced safely.
- Refresh run metadata is readable by ID.
- HTML endpoint has no report, stale report, and successful report behavior
  specified.
- Routes do not expose Jira authorization headers or tokens.

## Phase 2: Frontend Setup

### FE-001: Create React/Vite application shell

**Depends on:** None

**Work:**

1. Initialize React 18 and Vite.
2. Pin resolved package versions in package manifests and lockfiles.
3. Create feature-oriented source folders.
4. Add application layout and shared theme styles.
5. Add API client configuration.

**Acceptance criteria:**

- Frontend starts independently with Vite.
- Build and lint or type-check tasks complete.
- API base URL is environment-configured.
- API client does not accept or expose Jira credentials.

### FE-002: Add shared UI components

**Depends on:** FE-001

**Work:**

1. Create semantic layout components.
2. Create metric cards, status tables, issue lists, unavailable-value components,
   and refresh controls.
3. Add loading, empty, stale, and error presentations.
4. Add keyboard focus and visible focus states.

**Acceptance criteria:**

- Components render unavailable values distinctly from zero.
- Empty, loading, stale, and failure states are visually distinct.
- Controls are keyboard accessible.
- Components meet the repository responsive and accessibility conventions.

### FE-003: Add frontend routing

**Depends on:** FE-001

**Work:**

1. Add `/report`, `/configuration`, `/refresh/:runId`,
   `/report/preview`, and `/error` routes.
2. Add navigation and route-level fallback behavior.
3. Add route-level loading and error boundaries.

**Acceptance criteria:**

- Every documented route renders or redirects intentionally.
- Unknown routes show a safe fallback.
- Route transitions preserve the last successful report after refresh failure.
- Refresh failure does not relabel old report data as current.

### FE-004: Integrate configuration status screen

**Depends on:** BE-006, FE-002, FE-003

**Work:**

1. Fetch `/api/configuration/status`.
2. Render Jira, board, project, field, blocker, and secret-presence status.
3. Provide safe correction guidance.

**Acceptance criteria:**

- Secret values are never rendered or accepted through the UI.
- Invalid configuration is clearly identified.
- Valid configuration can be distinguished from missing Jira token configuration.

### FE-005: Integrate HTML report preview

**Depends on:** BE-007, FE-002, FE-003

**Work:**

1. Fetch or link to `/api/report/html`.
2. Render or open a standalone preview.
3. Provide no email, chat, Jira, or Confluence publishing action.

**Acceptance criteria:**

- Preview clearly labels the report as a draft.
- Preview reflects the latest successful report.
- No external distribution control is present.

## Phase 3: Feature Implementation

### FI-001: Implement configuration and secret handling

**Depends on:** BE-004, BE-005

**Work:**

1. Load `JIRA_BASE_URL`, `JIRA_ACCOUNT_EMAIL`, `JIRA_API_TOKEN`,
   `JIRA_PROJECT_KEY`, `JIRA_BOARD_ID`, `JIRA_STORY_POINT_FIELD_ID`,
   `JIRA_BLOCKED_STATUS`, `JIRA_BLOCKER_AGE_DAYS`, and
   `INCLUDE_ASSIGNEE_NAMES`.
2. Validate required values and HTTPS URL format.
3. Store only non-secret settings in `application_config`.
4. Add secret-presence status without secret exposure.

**Acceptance criteria:**

- Invalid configuration prevents Jira calls and report generation.
- The Jira token is loaded only in server memory at runtime.
- Database records contain no credential or authorization header.
- Logs contain no API token or account secret.

### FI-002: Implement Jira client

**Depends on:** FI-001

**Work:**

1. Implement Jira Cloud basic authentication from server-side email and token.
2. Implement HTTPS request, timeout, pagination, retries, and safe error
   mapping.
3. Bypass Jira writes and mutation endpoints.
4. Isolate Jira API code in an integration module.

**Acceptance criteria:**

- Authentication and permission failures return safe operation errors.
- Pagination retrieves all requested issues.
- HTTP 429 and 5xx retries are bounded.
- Jira mutation methods are absent or explicitly disabled.

### FI-003: Implement board and active-sprint retrieval

**Depends on:** FI-002

**Work:**

1. Retrieve the configured board.
2. Retrieve active sprints for that board.
3. Require exactly one active sprint.
4. Retrieve issues for the resolved sprint and configured project.

**Acceptance criteria:**

- Zero active sprints returns a clear failure.
- Multiple active sprints return an ambiguity failure.
- Only issues from the resolved active sprint and project are retained.
- Sprint ID, name, and dates are present or generation fails.

### FI-004: Normalize Jira issue data

**Depends on:** FI-003

**Work:**

1. Normalize issue key, summary, status, status category, assignee, issue type,
   story points, last-updated time, and Jira URL.
2. Identify mandatory and optional fields.
3. Reject partial required data.
4. Preserve missing story points as unavailable.

**Acceptance criteria:**

- Missing required issue fields stop report generation.
- Missing assignee is represented as unavailable or omitted as configured.
- Missing, invalid, and negative story points are not converted to zero.
- Jira text is normalized before rendering or persistence.

### FI-005: Implement status and issue metrics

**Depends on:** FI-004

**Work:**

1. Count exact Jira statuses and status categories.
2. Classify completed issues through Jira `Done` status category.
3. Calculate issue totals, completed, remaining, and completion percentage.
4. Mark empty-sprint issue completion unavailable.

**Acceptance criteria:**

- Status breakdown reflects exact returned active-sprint issues.
- Completion uses only `Done`, with no prototype allowlist override.
- The issue formula is completed / total.
- Empty sprint completion is unavailable, not zero.

### FI-006: Implement story-point metrics

**Depends on:** FI-004

**Work:**

1. Read the configured story-point custom field.
2. Accept only finite values greater than or equal to zero.
3. Calculate total, completed, remaining, and percentage values.
4. Report missing or invalid value count.

**Acceptance criteria:**

- Null, missing, invalid, non-finite, and negative values make affected totals
  unavailable.
- Zero is a valid story-point value.
- Percentage is completed points / current total points.
- Display values round to two decimal places.

### FI-007: Implement accomplishments and blockers

**Depends on:** FI-004, FI-005

**Work:**

1. Extract completed issues.
2. Match blocker status case-insensitively, defaulting to `Blocked`.
3. Apply the configured age threshold, defaulting to five days.
4. Sort accomplishments and blockers by issue key.
5. Describe last-updated only as an age signal.

**Acceptance criteria:**

- `Done` issues appear only in accomplishments.
- Exactly five-day and older `Blocked` issues appear in blockers.
- Newer blocked issues do not appear.
- Missing update timestamps are explicitly unavailable.

### FI-008: Implement deterministic executive summary

**Depends on:** FI-005, FI-006, FI-007

**Work:**

1. Generate the sprint identity and date summary.
2. Include issue totals and completion.
3. Include story-point availability.
4. Include highlighted blocker count.
5. Include UTC refresh timestamp and draft status.

**Acceptance criteria:**

- Summary contains only Jira-derived values.
- The template is deterministic for identical source data.
- No AI, forecast, root-cause, or blocker-history text is generated.

### FI-009: Implement standalone HTML report

**Depends on:** FI-005, FI-006, FI-007, FI-008

**Work:**

1. Render UTF-8 standalone HTML.
2. Include report title, timestamp, identity, summary, statuses, metrics,
   accomplishments, blockers, direct Jira links, and unavailable notices.
3. Escape every Jira-derived text value.
4. Add a 24-hour stale warning.
5. Add draft and manual-review labeling.

**Acceptance criteria:**

- HTML opens without Express or any server.
- Script-like Jira text is escaped.
- Direct Jira links are valid and safe.
- Stale reports retain the original timestamp and display a warning.
- Report contains no token or authorization header.

### FI-010: Implement refresh workflow and atomic replacement

**Depends on:** BE-005, FI-003, FI-004, FI-005, FI-006, FI-007, FI-008, FI-009

**Work:**

1. Create a refresh run with `running` status.
2. Run the complete Jira and metrics pipeline.
3. Create the report snapshot and child records.
4. Replace latest report state and child rows in one transaction.
5. Mark run `completed` or `failed`.
6. Prevent overlapping refresh operations.

**Acceptance criteria:**

- Success replaces latest report and child rows atomically.
- Failure updates only run metadata and preserves latest report rows.
- Concurrent refresh requests cannot create duplicate active runs.
- Run response contains no secret or raw Jira response.

### FI-011: Implement report API and HTML preview

**Depends on:** BE-007, FI-010

**Work:**

1. Connect `/api/report`, `/api/report/html`, and `/api/report/runs/:runId`
   to latest report and run services.
2. Add response DTOs and stale report metadata.
3. Set secure HTML response headers and download behavior.

**Acceptance criteria:**

- API DTO matches the specification.
- HTML preview/download contains only the latest successful report.
- Stale and no-report states are explicit.
- No credential or secret appears in response data.

## Phase 4: Integration and Testing

### IT-001: Connect frontend to backend

**Depends on:** FE-004, FE-005, BE-006, BE-007

**Work:**

1. Wire report, configuration, refresh, preview, and run-result screens.
2. Define loading, success, stale, no-report, and failure state behavior.
3. Preserve the previous successful report on refresh failure.

**Acceptance criteria:**

- All documented frontend flows call the correct backend endpoints.
- Failed refresh does not relabel old report data as current.
- UI displays unavailable values and safe error text.

### IT-002: Add backend unit tests

**Depends on:** FI-002, FI-003, FI-004, FI-005, FI-006, FI-007, FI-008, FI-009

**Work:**

1. Test configuration validation.
2. Test Jira normalization and active-sprint handling.
3. Test pagination and no-progress detection.
4. Test status, completion, story-point, blocker, and summary rules.
5. Test HTML escaping and credential redaction.

**Acceptance criteria:**

- Unit tests pass without live Jira credentials.
- Exactly-five-day, missing-point, empty-sprint, and malformed-response cases
  have focused tests.
- Token values and authorization headers are absent from test output and
  rendered content.

### IT-003: Add backend integration tests

**Depends on:** BE-005, FI-010

**Work:**

1. Test migrations and repositories against PostgreSQL.
2. Test Jira fixture or isolated-workspace authentication and retrieval.
3. Test refresh success and failure.
4. Test concurrent refresh prevention.
5. Test API validation and error schemas.

**Acceptance criteria:**

- Integration tests isolate test database and Jira fixtures.
- A failed refresh leaves latest report rows unchanged.
- HTTP responses use documented status and error bodies.
- No test mutates production Jira or Confluence data.

### IT-004: Add frontend tests

**Depends on:** FE-002, FE-003, FE-004, FE-005, IT-001

**Work:**

1. Test report loading and success.
2. Test no-report, stale, configuration, refresh, and error states.
3. Test keyboard controls and unavailable-value rendering.

**Acceptance criteria:**

- Focused UI tests pass for all documented states.
- Refresh failure preserves previous report UI.
- No secret-bearing field or distribution action is exposed.

### IT-005: Run Docker Compose end-to-end

**Depends on:** BE-001, BE-002, BE-003, BE-004, BE-005, BE-006, BE-007, FE-001, FE-002, FE-003, FE-004, FE-005

**Work:**

1. Start PostgreSQL, backend, and frontend through Docker Compose.
2. Verify migrations and service health.
3. Verify frontend-to-backend connectivity.
4. Test clean startup and restart behavior.

**Acceptance criteria:**

- One documented Compose command starts the complete local application.
- Health endpoint reports database readiness.
- Frontend loads report and configuration states.
- Restart preserves only the intended latest successful report state.

### IT-006: Run security and reliability checks

**Depends on:** FI-001, FI-002, FI-009, FI-010

**Work:**

1. Scan API responses, HTML, and logs for credential leakage.
2. Verify HTTPS Jira traffic.
3. Verify CORS and security headers.
4. Verify report replacement under injected failures.
5. Verify Docker database credentials are not exposed.

**Acceptance criteria:**

- No Jira token or authorization header appears in logs or output.
- Failure injection leaves the previous report intact.
- HTTPS and approved CORS behavior are verified.
- HTML text escaping blocks script-like Jira content.

### IT-007: Verify performance and acceptance

**Depends on:** IT-002, IT-003, IT-004, IT-005, IT-006

**Work:**

1. Run normal report refresh fixture and optional live Jira smoke test.
2. Verify normal refresh completion under five minutes.
3. Verify report content against acceptance criteria.
4. Perform manual desktop and narrow-width review.

**Acceptance criteria:**

- Normal refresh completes in under five minutes.
- Issue and story-point metrics match Jira fixtures.
- Status, accomplishments, blockers, and direct links are present.
- No Jira issue or Confluence content is mutated.
- Release candidate passes manual review.

## Milestones

| Milestone | Task dependencies | Exit criteria |
|---|---|---|
| M1 Database and API skeleton | BE-001, BE-002, BE-003, BE-004, BE-005, BE-006, BE-007 | PostgreSQL, migrations, and Express routes start in Docker |
| M2 Frontend skeleton | FE-001, FE-002, FE-003, FE-004, FE-005 | React routes and shared API states render |
| M3 Jira retrieval | FI-001, FI-002, FI-003, FI-004 | Jira fixtures resolve one sprint and normalize issues |
| M4 Report features | FI-005, FI-006, FI-007, FI-008, FI-009, FI-010, FI-011 | Metrics, HTML, and atomic refresh replacement work |
| M5 Integrated application | IT-001, IT-002, IT-003, IT-004, IT-005 | Frontend/backend/Docker flows pass |
| M6 Release candidate | IT-006, IT-007 | Security, performance, tests, and manual review pass |

## Definition of Done

The implementation is complete when all tasks in each milestone satisfy their
acceptance criteria and:

1. Docker Compose starts PostgreSQL, Express, and React.
2. A configured Manager can manually refresh one Jira active sprint.
3. The UI and HTML contain accurate status and work metrics.
4. Missing story points and missing sprint data are explicitly unavailable.
5. Failed refreshes preserve the latest successful report.
6. Jira credentials never appear in logs, database, API responses, or HTML.
7. No Jira or Confluence write occurs.
8. No email, chat, Jira, Confluence, or other distribution operation occurs.
