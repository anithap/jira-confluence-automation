# Implementation Plan: Jira/Confluence Automation Web Application

**Specification:** [specification.md](specification.md)
**Clarifications:** [clarify.md](clarify.md)
**Constitution:** [constitution.md](constitution.md)
**Status:** Planned web application; supersedes the earlier CLI prototype sequencing

## 1. Objective

Build a full-stack Jira/Confluence automation application using:

- React 18 and Vite
- Node.js v26.13.1 and Express
- npm 11.20.0
- PostgreSQL 15
- Docker and Docker Compose
- Jira Cloud REST APIs
- Optional Confluence integration only after the Jira feature is complete

The first delivered feature is a Jira sprint status dashboard and report
workflow for a Manager. Confluence writes, automated distribution, Jira writes,
and multi-tenant administration remain disabled unless a later specification
explicitly enables them.

## 2. Architecture

```text
React 18 / Vite
      |
      | JSON/HTTPS
      v
Express API
      |
      +--> Jira integration service
      +--> Report and metrics service
      +--> PostgreSQL repositories
      +--> HTML report renderer
      |
      v
PostgreSQL 15
```

Responsibilities:

- React owns presentation, navigation, loading states, and review actions.
- Express owns authentication policy, validation, Jira access, calculations,
  and HTTP error handling.
- Jira integration code owns API authentication, pagination, normalization,
  retries, and source access.
- PostgreSQL stores configuration metadata, refresh runs, latest report state,
  status counts, and report issue rows.
- Jira API tokens and account credentials stay server-side.

## 3. Phase 1: Backend Setup

### 3.1 Database setup

Work:

1. Add a PostgreSQL 15 service to Docker Compose.
2. Add a migration runner and versioned migration files.
3. Create the initial entities:
   - `application_config`
   - `refresh_run`
   - `latest_report`
   - `latest_status_count`
   - `latest_report_issue`
4. Add foreign keys, indexes, uniqueness constraints, and transaction helpers.
5. Add environment variables for database host, port, name, user, and password.
6. Add startup validation and a readiness health check.
7. Ensure migrations run without exposing credentials in logs.

Milestone:

- PostgreSQL starts reproducibly through Docker Compose.
- A clean database can be migrated and reset in development.
- The application cannot start with invalid database configuration.

### 3.2 API skeleton

Work:

1. Create the Express application entry point and environment loader.
2. Add focused route modules for health, configuration, reports, and refresh
   runs.
3. Add JSON parsing, input validation, CORS rules, security headers, and
   centralized error handling.
4. Add request IDs and credential-safe structured logging.
5. Add service and repository interfaces before implementing Jira calls.
6. Add HTTP authentication policy for the configured deployment mode.

Required endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Backend and database readiness |
| `GET` | `/api/configuration/status` | Non-secret configuration status |
| `GET` | `/api/report` | Latest successful report |
| `POST` | `/api/report/refresh` | Trigger a manual refresh |
| `GET` | `/api/report/html` | Standalone HTML preview or download |
| `GET` | `/api/report/runs/:runId` | Refresh-run result |

Milestone:

- Express starts with Docker Compose.
- Health and configuration endpoints return documented JSON.
- Invalid requests use a consistent error schema.
- No credentials or authorization headers are returned or logged.

## 4. Phase 2: Frontend Setup

### 4.1 UI skeleton

Work:

1. Create the React 18 application with Vite.
2. Add feature-oriented folders for report, configuration, and refresh state.
3. Add a shared API client that never receives Jira credentials.
4. Add an application layout, navigation, page titles, loading states, and
   application error boundaries.
5. Add reusable components for status cards, status tables, issue lists,
   unavailable values, and refresh controls.
6. Add semantic HTML and responsive CSS.

### 4.2 Routing

Routes:

- `/` or `/report`: latest sprint report
- `/configuration`: non-secret configuration status
- `/refresh/:runId`: refresh progress and result
- `/report/preview`: standalone HTML preview
- `/error`: application error fallback

Milestone:

- The frontend starts independently under Vite.
- Routes render loading, success, no-report, and error states.
- API failures remain visible without exposing technical secrets.
- UI components are keyboard accessible and responsive.

## 5. Phase 3: Feature Implementation

Implement one end-to-end feature at a time.

### Feature 1: Configuration and security

Implementation:

1. Load Jira and database configuration from environment variables.
2. Validate the Jira base URL, project key, board ID, story-point field, blocked
   status, blocker threshold, and assignee setting.
3. Store only non-secret configuration in PostgreSQL.
4. Read the Jira API token and account email at runtime.
5. Return `jiraTokenConfigured` without returning the token.

Acceptance:

- Invalid configuration fails before Jira or report operations.
- Configuration status is visible through the API and UI.
- Secrets never enter database, logs, responses, or HTML.

### Feature 2: Jira sprint retrieval

Implementation:

1. Authenticate to Jira Cloud with HTTPS.
2. Resolve the configured board.
3. Reject zero or multiple active sprints.
4. Retrieve all sprint issues using pagination.
5. Normalize required Jira fields and validate partial responses.
6. Apply bounded retries and request limits.

Acceptance:

- Exactly one active sprint produces a complete snapshot.
- Zero or multiple active sprints produce safe failures.
- Pagination covers every required issue.
- Unit tests use fixtures instead of live credentials.

### Feature 3: Sprint metrics

Implementation:

1. Count issues by exact status and status category.
2. Classify completion using Jira's `Done` status category.
3. Calculate completed, remaining, and total issues.
4. Calculate story-point totals, completed points, remaining points, and
   percentages.
5. Mark missing, invalid, negative, or non-finite story points unavailable.
6. Calculate blockers for configured status and five-day default threshold.
7. Produce a deterministic executive summary.

Acceptance:

- Missing points are not converted to zero.
- Exactly-five-day blockers are highlighted.
- Empty sprints show unavailable percentages.
- Metrics are deterministic for the same Jira snapshot.

### Feature 4: Report preview and download

Implementation:

1. Build a standalone HTML report with the sprint sections defined in the
   specification.
2. Escape Jira-provided text.
3. Preserve the latest successful report after a failed refresh.
4. Return HTML preview/download content from the API.
5. Mark failed or stale data clearly.

Acceptance:

- HTML opens without a server.
- Jira text cannot add executable markup.
- Failed refreshes do not change the latest report.
- Reports older than 24 hours display a stale warning.

### Feature 5: Manual refresh workflow

Implementation:

1. Create a refresh run in PostgreSQL with `running` status.
2. Run Jira retrieval and calculations.
3. Replace latest report and child rows in one database transaction.
4. Mark the run `completed` or `failed`.
5. Return safe progress and error details.
6. Prevent overlapping refresh requests.

Acceptance:

- A successful refresh replaces only the latest report state.
- A failed refresh updates run metadata but preserves latest report rows.
- Concurrency cannot create duplicate active refresh runs.

## 6. Phase 4: Integration and Testing

### 6.1 Integration work

1. Connect frontend pages to backend endpoints.
2. Verify configuration, report, refresh, preview, and run-result flows.
3. Verify Docker Compose starts PostgreSQL, backend, and frontend consistently.
4. Verify migrations, readiness checks, CORS, and security headers.
5. Verify CLI or scheduled refresh integration only if an approved entry point
   is retained.
6. Verify no Jira mutations or Confluence writes occur.

### 6.2 Automated testing

Backend unit tests:

- Configuration validation
- Jira response normalization
- Active-sprint ambiguity
- Pagination
- Status and completion calculations
- Story-point missing-data behavior
- Blocker threshold
- HTML escaping
- Credential redaction
- Atomic database replacement

Backend integration tests:

- PostgreSQL migrations and repositories
- Jira fixtures or isolated test workspace
- Refresh success and failure
- Concurrent refresh prevention
- API validation and error bodies

Frontend tests:

- Loading, success, no-report, stale, and failure states
- Configuration status
- Refresh progress and result
- Accessible controls and links
- Responsive report presentation

Acceptance testing:

- A configured active sprint produces a report in under five minutes.
- Status breakdown, issue completion, story points, accomplishments, and
  blockers are accurate.
- Exactly one active sprint is required.
- Missing data is explicit.
- Failed refreshes preserve the latest report.
- HTML contains no credentials.
- No Jira or Confluence content is modified.

### 6.3 Performance and security checks

1. Bound Jira pagination, retries, request timeouts, and refresh duration.
2. Measure normal refresh under five minutes.
3. Verify HTTPS Jira traffic.
4. Verify CORS and HTTP security headers.
5. Check logs and responses for tokens or authorization headers.
6. Verify database credentials are not exposed to the frontend.
7. Verify report text is escaped in API and HTML contexts.

## 7. Milestones

| Milestone | Exit criteria |
|---|---|
| M1 Database and API skeleton | PostgreSQL migrations and documented Express endpoints run in Docker |
| M2 Frontend skeleton | React routes and shared API integration render core states |
| M3 Jira retrieval | Board, active sprint, pagination, and normalization pass fixtures |
| M4 Report features | Metrics, preview, and report replacement are complete |
| M5 Integrated application | Frontend and backend pass end-to-end refresh flows |
| M6 Release candidate | Tests, security checks, Docker startup, and manual review pass |

## 8. Implementation Order

1. Database migrations and repository interfaces
2. Express application and health/configuration endpoints
3. React shell and route structure
4. Jira board, active-sprint, and issue integration
5. Metrics and report domain services
6. PostgreSQL latest-report replacement
7. Report HTML preview/download
8. Manual refresh UI and API workflow
9. Integration tests, security checks, and Docker verification

## 9. Validation and Traceability

| Spec area | Implementation coverage |
|---|---|
| Project architecture | React/Vite, Express, PostgreSQL, Docker |
| Jira sprint | Board, active sprint, and paginated issue retrieval |
| Report metrics | Status, completion, story points, accomplishments, blockers |
| Data retention | Latest successful report and bounded refresh metadata |
| UI | Report, configuration, refresh, preview, and error screens |
| Security | Server-side credentials, HTTPS, escaping, secret redaction |
| Reliability | Atomic database replacement and previous-report preservation |
| Out of scope | No Jira edits, Confluence writes, or external distribution |

## 10. Out of Scope

The implementation plan does not include:

- Jira issue or sprint edits
- Confluence page reads or writes
- Email, Slack, Teams, or Jira distribution
- Historical sprint reporting
- Multi-board or cross-team reporting
- Historical story-point burnup
- Jira OAuth or multi-user login
- Generative AI reports
- Public internet deployment

## 11. Definition of Done

The application is complete when:

1. Docker Compose starts PostgreSQL, backend, and frontend locally.
2. Migrations, repositories, Express routes, and React routes are implemented.
3. The Manager can manually refresh one configured active sprint.
4. The UI and standalone report show accurate sprint metrics.
5. Missing values are clearly unavailable.
6. Failed refreshes preserve the latest successful report.
7. API and HTML output contain no credentials.
8. Automated tests cover backend, frontend, integration, and security behavior.
9. Jira and Confluence writes remain disabled.
