# Feature Specification: Jira Sprint Status Automation

**Project:** Jira/Confluence Automation
**Feature:** Daily Jira Active-Sprint Status Report
**Status:** Draft
**Constitution:** [constitution.md](constitution.md)
**Source specifications:** [project_spec.md](../project_spec.md), [requirements.md](../requirements.md)

## 1. Summary

Build a secure automation that reads one Jira Cloud Scrum board's active sprint
and produces a deterministic, standalone HTML status report for a Manager
responsible for a 10-person Development and Support team.

The report supports delivery-health, blocker, accomplishment, and stakeholder-
status review. It must be generated locally and require human review before
distribution. The automation must not edit Jira, publish to Confluence, email
the report, or distribute it through another system.

## 2. Goals

- Generate the current-sprint status report in under five minutes.
- Report issue counts, status distribution, completion, story points,
  completed work, and highlighted blockers accurately.
- Support both daily scheduled execution and manual execution.
- Preserve the previous report when Jira, configuration, or authentication
  fails.
- Keep Jira credentials outside source control and generated output.
- Make missing or unavailable Jira data explicit instead of inventing values.

## 3. Non-Goals

The initial implementation must not:

- Edit Jira issues or sprint settings.
- Publish or update Confluence pages.
- Email or automatically distribute reports.
- Post reports to Teams, Slack, Jira, or another service.
- Provide a hosted or publicly accessible dashboard.
- Add historical sprint reporting or snapshots.
- Aggregate multiple boards, projects, or teams.
- Infer issue blocker history.
- Use generative AI to create report narratives.
- Support automatic polling or real-time Jira updates.

## 4. Target Users

| Role | Responsibility |
|---|---|
| Manager | Runs or requests the report and reviews it before manual sharing |
| Development and Support team | Maintains Jira status and issue metadata |
| Stakeholders | Consume only manually approved report content |
| Jira/Confluence administrator | Authorizes integrations and write permissions |

Assignee names may appear only when configuration permits it. Stakeholders
must not receive raw Jira API responses or credential-bearing data.

## 5. System Context

```text
Manager or Windows Scheduled Task
              |
              v
Configuration and Secrets
              |
              v
Jira Cloud REST API
              |
              v
Sprint and Issue Normalizer
              |
              v
Deterministic Metrics Engine
              |
              v
Standalone HTML Report
```

The primary source system is Jira Cloud:

- Base URL: `https://anitharanip.atlassian.net`
- Candidate project key: `SAM1`
- One configured Scrum board
- One resolved active sprint
- Jira API token and account email loaded through secure configuration

The board ID, project key, and Jira story-point custom field ID must be
confirmed by configuration. Candidate values must not be silently promoted to
production configuration.

## 6. Technology Constraints

The implementation must follow [constitution.md](constitution.md):

- Frontend: React 18.x with Vite
- Backend: Node.js v26.13.1 with Express
- Package manager: npm 11.20.0
- Runtime manager: nvm 1.2.2
- Database: PostgreSQL 15.x
- Infrastructure: Docker 29.9.3 and Docker Compose
- Atlassian integrations: Jira Cloud REST API; Confluence integration is not
  required for the MVP

Package manifests and lockfiles must pin supporting dependencies. PostgreSQL
must be available for the target application architecture even though the MVP
does not require historical sprint snapshots.

The CLI report may be a local entry point to the same backend services rather
than a separate implementation. Python-based alternatives must not replace the
Node.js/Express architecture defined by the constitution.

## 7. User Stories

### US-1: Generate a Sprint Report

**As** a Manager,
**I want** to generate a status report for the active sprint,
**so that** I can review delivery health and blockers without manually
assembling Jira data.

**Acceptance:** The report is created locally, contains all required sections,
and identifies its sprint, project, board, and data refresh time.

### US-2: Refresh on a Schedule

**As** a Manager,
**I want** the report to refresh at a selected local time each day,
**so that** a current draft is available for review.

**Acceptance:** A Windows scheduled task can execute the same refresh logic as
manual execution.

### US-3: Refresh Manually

**As** a Manager,
**I want** to refresh outside the scheduled time,
**so that** I can obtain the latest report before a stakeholder meeting.

**Acceptance:** Manual execution does not depend on the scheduled task.

### US-4: Identify Completed Work

**As** a Manager,
**I want** completed issues and completion percentages visible in the report,
**so that** I can assess current sprint delivery.

**Acceptance:** Jira issues are complete only when their status category is
`Done`, unless an explicitly approved allowlist is configured.

### US-5: Identify Blockers

**As** a Manager,
**I want** long-standing `Blocked` issues highlighted,
**so that** I can prioritize follow-up.

**Acceptance:** An issue appears only when status is exactly `Blocked`
(case-insensitive) and last-updated is at least five days old.

### US-6: Recover from Jira Failure

**As** a Manager,
**I want** the previous report preserved when Jira fails,
**so that** I do not accidentally replace accurate output with an incomplete
draft.

**Acceptance:** The failed operation emits a clear error and does not modify
the previous report.

## 8. Functional Requirements

### FR-001: Load and Validate Configuration

The system must load configuration and secrets from environment variables or
a local secret store.

Required values:

- Jira base URL
- Jira account email
- Jira API token environment-variable name
- Jira project key
- Jira numeric board ID
- Jira story-point custom field ID
- Blocked status name or identifier
- Blocker age threshold
- Report output path
- Assignee-name inclusion setting

Invalid, missing, or ambiguous configuration must stop execution with an
operation-specific error.

### FR-002: Authenticate to Jira Cloud

The backend must use HTTPS and Jira Cloud authentication.

The system must:

- Read the configured API token at runtime.
- Reject missing credentials.
- Treat authentication failures as fatal.
- Never log authorization headers or token values.

### FR-003: Resolve the Active Sprint

The system must:

1. Retrieve the configured Scrum board.
2. Resolve exactly one active sprint for that board.
3. Reject zero active sprints.
4. Reject multiple ambiguous active sprints.
5. Record the resolved sprint ID, name, start date, and end date.

Arbitrary selection among multiple active sprints is prohibited.

### FR-004: Retrieve Sprint Issues

The system must retrieve all issues in the resolved sprint using Jira pagination.

Required normalized fields:

- Issue key
- Summary
- Status
- Status category
- Assignee name
- Issue type
- Story points
- Last-updated timestamp
- Jira web link
- Sprint identity

No partial Jira response may be used to generate a report.

### FR-005: Generate the Executive Summary

The report must include:

- Sprint name
- Sprint date range
- Project key
- Board ID
- Data refresh timestamp
- Completed issue count
- Remaining issue count
- Blocker summary
- Concise stakeholder-facing status narrative derived only from calculated
  values

The narrative must not invent facts, causes, forecasts, or risk history.

### FR-006: Show Status Breakdown

The report must show issue counts by:

- Exact Jira status
- Jira status category

Counts must include only issues in the active sprint. The status breakdown must
remain available when story-point values are missing.

### FR-007: Calculate Issue Completion

An issue is complete when its Jira status category is `Done`.

The report must calculate:

- Total issue count
- Completed issue count
- Remaining issue count
- Completion percentage

The formula is:

```text
completed issue count / total issue count
```

If there are no issues, issue completion percentage must be shown as unavailable.

### FR-008: Calculate Story-Point Progress

Story points must come from the configured Jira custom field.

The report must calculate:

- Total story points
- Completed story points
- Remaining story points
- Completed story-point percentage

Missing, invalid, or negative values must not be treated as zero. If any value
prevents an accurate calculation, totals and affected percentages must be
marked unavailable and the count of missing values must be identified.

### FR-009: List Completed Accomplishments

The report must list issues classified as complete.

Each accomplishment must include:

- Issue key
- Summary
- Assignee when available and permitted
- Direct Jira issue link

Accomplishments must not be inferred from stale or partial data.

### FR-010: Highlight Blockers and Risks

An issue is highlighted as a blocker only when:

- Its status is exactly `Blocked`, compared case-insensitively.
- Its Jira last-updated timestamp is at least five days before refresh time.

The report must include issue key, summary, assignee when available, status,
last-updated timestamp, and direct Jira link.

The system must state “no blocker highlighted” if no issue meets the rules.
Last-updated must be described only as an age signal and must not be interpreted
as blocked-start history.

### FR-011: Render Standalone HTML

The report must:

- Open directly in a browser without a server.
- Use responsive desktop and mobile styling.
- Escape all Jira-provided text before rendering.
- Render direct Jira issue links safely.
- Contain no credentials, authorization headers, or secret values.
- Use a clear unavailable state for missing data.

The previous report must remain unchanged until generation completes
successfully.

### FR-012: Write the Report Atomically

After all required Jira responses and calculations succeed, the system must
write the report through a temporary file and atomic replacement when supported
by the operating system.

A refresh failure must preserve the existing report.

### FR-013: Support Manual and Daily Execution

The system must support:

- Manual command-line execution.
- A Windows scheduled task at a user-selected local time.
- The same configuration, validation, Jira, calculation, and rendering logic
  for both entry points.

Manual execution must remain available independently of scheduling.

### FR-014: Prevent External Actions

The MVP must not automatically:

- Edit Jira issues or sprint metadata.
- Publish to Confluence.
- Send email.
- Post to chat or collaboration systems.
- Share or upload the report.

It must produce a local draft for human review.

### FR-015: Handle Failures Safely

On configuration, authentication, board, sprint, pagination, API, validation,
or report-generation failure, the system must:

1. Stop the affected operation.
2. Print or log a concise operation-specific error.
3. Avoid logging credentials or authorization headers.
4. Preserve the previous report.
5. Avoid generating fabricated metrics.

## 9. API and Internal Interface Requirements

The React/Vite frontend communicates with Express through JSON REST endpoints.
Atlassian credentials, Jira API calls, and secret configuration must remain
server-side. The API must not return Jira authorization headers or secret
values.

### Endpoint Summary

| Method | Endpoint | Purpose | Request data | Response data |
|---|---|---|---|---|
| `GET` | `/health` | Check backend availability | None | Service status and timestamp |
| `GET` | `/api/configuration/status` | Show whether required non-secret configuration is valid | None | Configuration fields with secret names masked |
| `POST` | `/api/report/refresh` | Start a manual Jira refresh | Optional refresh reason/source | Run ID, status, and accepted timestamp |
| `GET` | `/api/report` | Return the latest successful report state | None | Sprint metrics, issue lists, timestamps, and source IDs |
| `GET` | `/api/report/html` | Return or download the standalone report | Optional download flag | HTML content or HTML download |
| `GET` | `/api/report/runs/:runId` | Inspect a refresh operation | Run ID path parameter | Run status, timestamp, and safe error details |

### `GET /health`

Returns backend readiness without exposing secrets or Jira data.

```json
{
  "status": "ready",
  "timestamp": "2026-11-23T10:00:36.906+05:30"
}
```

The endpoint must return `503` with a non-secret status reason if required
services are unavailable.

### `GET /api/configuration/status`

Returns only non-secret configuration and validation status. Secret values
must never be returned.

```json
{
  "isValid": true,
  "jiraBaseUrl": "https://anitharanip.atlassian.net",
  "projectKey": "SAM1",
  "boardId": 12345,
  "storyPointFieldId": "customfield_10000",
  "blockedStatus": "Blocked",
  "blockerAgeThresholdDays": 5,
  "includeAssigneeNames": true,
  "jiraTokenConfigured": true
}
```

`500` or `422` is returned for a configuration that cannot safely be used.

### `POST /api/report/refresh`

Starts a Jira refresh and stores no token or Jira authorization header.

Request:

```json
{
  "source": "manual"
}
```

Response:

```json
{
  "runId": "c3a8f5dc-5e8b-4e37-9fbb-14d8cb5f6c21",
  "status": "completed",
  "startedAt": "2026-11-23T10:00:36.906+05:30",
  "completedAt": "2026-11-23T10:00:42.121+05:30"
}
```

Successful refreshes return `200`. A validation or Jira failure returns `502`
or `422` with a safe operation-specific message and leaves the latest report
unchanged.

### `GET /api/report`

Returns the latest successful report DTO:

```json
{
  "runId": "c3a8f5dc-5e8b-4e37-9fbb-14d8cb5f6c21",
  "dataTimestamp": "2026-11-23T10:00:42.121+05:30",
  "sprint": {
    "id": 1001,
    "name": "Sprint 42",
    "startDate": "2026-11-16",
    "endDate": "2026-11-29"
  },
  "projectKey": "SAM1",
  "boardId": 12345,
  "metrics": {
    "totalIssues": 20,
    "completedIssues": 12,
    "remainingIssues": 8,
    "issueCompletionPercentage": 60,
    "totalStoryPoints": 55,
    "completedStoryPoints": 34,
    "remainingStoryPoints": 21,
    "storyPointCompletionPercentage": 61.82
  },
  "statusCounts": [],
  "statusCategoryCounts": [],
  "completedIssues": [],
  "highlightedBlockers": []
}
```

Story-point metrics and their percentages must be `null` when unavailable.
Missing-value counts must be returned separately instead of replacing missing
values with zero.

### `GET /api/report/html`

Returns the standalone report HTML or a downloadable attachment when requested.
The response must contain no API credentials and must retain the last successful
report after refresh failures.

### `GET /api/report/runs/:runId`

Returns run metadata only:

```json
{
  "runId": "c3a8f5dc-5e8b-4e37-9fbb-14d8cb5f6c21",
  "source": "manual",
  "status": "failed",
  "startedAt": "2026-11-23T10:00:36.906+05:30",
  "completedAt": "2026-11-23T10:00:38.002+05:30",
  "error": {
    "operation": "jira_active_sprint_lookup",
    "message": "Unable to resolve exactly one active sprint."
  }
}
```

Implementation must apply CORS only to approved origins, add appropriate
HTTP security headers, redact credentials in logs and errors, and isolate Jira
API access behind the backend integration module.

## 10. UI Screens

The React/Vite frontend is a review and refresh interface for the report.
It must not expose source credentials or raw Jira API responses.

### Screen: Main Report

Purpose: let the Manager review the latest successful sprint report.

Required content:

- Sprint name and date range
- Project and board identifiers
- Latest successful Jira data timestamp
- Issue completion total and percentage
- Story-point completion or unavailable state
- Status breakdown by exact Jira status
- Status-category breakdown
- Completed accomplishments
- Highlighted blockers
- Direct Jira issue links
- Manual refresh action
- Last refresh status

States:

- Loading the latest report
- Successful report
- No report available
- Refresh in progress
- Refresh failed with preserved previous report
- Data fields unavailable or missing

The report must clearly indicate that it is a draft requiring human review
before manual distribution.

### Screen: Configuration Status

Purpose: make configuration readiness visible without showing secrets.

Required content:

- Jira base URL
- Project key
- Board ID
- Story-point field ID
- Blocker status and age threshold
- Assignee-name setting
- Whether the Jira token is configured
- Configuration validity
- Safe correction guidance

The screen must not provide a field that submits, displays, or returns a Jira
API token.

### Screen: Refresh Progress and Result

Purpose: show the outcome of a manual refresh.

Required content:

- Refresh start and completion time
- Operation status
- Jira lookup stage
- Safe error message
- Link or action to view the previous successful report
- Retry action

On failure, the previous report remains visible and its data timestamp must
remain unchanged. The screen must not imply that failed data has become current.

### Screen: HTML Report Preview

Purpose: provide a browser view of the standalone report before distribution.

Required behavior:

- Render the server-generated, escaped HTML in a controlled preview area or
  open it as a standalone document.
- Provide a download or open action.
- State that the report is a draft.
- Provide no automatic email, chat, Jira, or Confluence publish action.

### Screen: Error State

Purpose: communicate configuration or source-system failures without leaking
technical secrets.

Required behavior:

- Identify the failed operation.
- Describe the safe next step.
- Preserve previously loaded report content.
- Offer manual retry only after the configuration or source issue is resolved.

The UI must use semantic HTML, visible focus states, keyboard controls,
responsive layouts, and clear unavailable/error states.

## 11. Data Model

PostgreSQL 15 stores the latest successful report state and bounded refresh
audit metadata. The MVP does not require historical Jira issue snapshots.
The application must retain only the latest successful report and must not
present older data as current.

### Database Entities

#### `application_config`

Stores non-secret application settings and validation status.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Stable configuration record |
| `jira_base_url` | VARCHAR | Jira Cloud base URL |
| `project_key` | VARCHAR | Configured Jira project key |
| `board_id` | BIGINT | Configured Scrum board ID |
| `story_point_field_id` | VARCHAR | Jira custom field ID |
| `blocked_status` | VARCHAR | Blocker status name |
| `blocker_age_threshold_days` | INTEGER | Minimum blocker age |
| `include_assignee_names` | BOOLEAN | Whether assignee names may be shown |
| `output_path` | TEXT | Local standalone HTML path |
| `is_valid` | BOOLEAN | Configuration validation result |
| `updated_at` | TIMESTAMPTZ | Last configuration update |

API credential names and secrets must not be stored in this table. Jira API
tokens remain environment or local secret-store values.

#### `refresh_run`

Records manual or scheduled refresh attempts.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Run identifier |
| `source` | VARCHAR | `manual` or `scheduled` |
| `status` | VARCHAR | `running`, `completed`, or `failed` |
| `started_at` | TIMESTAMPTZ | Run start time |
| `completed_at` | TIMESTAMPTZ | Run end time |
| `error_operation` | VARCHAR | Safe operation identifier |
| `error_message` | TEXT | Redacted error message |

No authorization header, API token, response body, or raw secret is stored.

#### `latest_report`

Stores the latest successful calculated report.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | One-row latest-report identifier |
| `refresh_run_id` | UUID | Successful run reference |
| `sprint_id` | BIGINT | Jira sprint ID |
| `sprint_name` | VARCHAR | Jira sprint name |
| `sprint_start_date` | DATE | Sprint start date |
| `sprint_end_date` | DATE | Sprint end date |
| `project_key` | VARCHAR | Jira project key |
| `board_id` | BIGINT | Jira board ID |
| `data_timestamp` | TIMESTAMPTZ | Successful Jira refresh time |
| `total_issue_count` | INTEGER | Total sprint issues |
| `completed_issue_count` | INTEGER | Jira `Done` issues |
| `remaining_issue_count` | INTEGER | Remaining issues |
| `issue_completion_percentage` | NUMERIC | Nullable issue percentage |
| `total_story_points` | NUMERIC | Nullable accurate total |
| `completed_story_points` | NUMERIC | Nullable completed total |
| `remaining_story_points` | NUMERIC | Nullable remaining total |
| `story_point_completion_percentage` | NUMERIC | Nullable story-point percentage |
| `missing_story_point_count` | INTEGER | Count of missing or invalid values |
| `executive_summary` | TEXT | Deterministic summary |
| `html_path` | TEXT | Local report path |
| `created_at` | TIMESTAMPTZ | Report persistence time |

#### `latest_status_count`

Stores status and status-category counts for the latest successful report.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Count row identifier |
| `latest_report_id` | UUID | Report relationship |
| `dimension` | VARCHAR | `status` or `status_category` |
| `dimension_name` | VARCHAR | Exact Jira status or category name |
| `issue_count` | INTEGER | Count for the dimension |

#### `latest_report_issue`

Stores issue details needed by completed-accomplishment and blocker views.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Database issue row |
| `latest_report_id` | UUID | Report relationship |
| `issue_key` | VARCHAR | Jira issue key |
| `summary` | TEXT | Jira issue summary |
| `status_name` | VARCHAR | Jira status |
| `status_category` | VARCHAR | Jira status category |
| `assignee_name` | VARCHAR | Nullable permitted assignee |
| `issue_type` | VARCHAR | Jira issue type |
| `story_points` | NUMERIC | Nullable or unavailable story points |
| `last_updated` | TIMESTAMPTZ | Jira last-updated timestamp |
| `jira_url` | TEXT | Direct Jira issue link |
| `is_completed` | BOOLEAN | Whether status category is `Done` |
| `is_highlighted_blocker` | BOOLEAN | Whether blocker rules matched |

### Entity Relationships

```text
application_config
        |
        | configuration context
        v
refresh_run --1:1--> latest_report
                         |
                         +--1:N--> latest_status_count
                         |
                         +--1:N--> latest_report_issue
```

- `refresh_run.refresh_run_id` identifies the successful run associated with
  `latest_report.refresh_run_id`.
- `latest_status_count.latest_report_id` belongs to exactly one latest report.
- `latest_report_issue.latest_report_id` belongs to exactly one latest report.
- A successful refresh replaces the latest report and its related latest status
  and issue rows in one transaction.
- A failed refresh inserts or updates run metadata only and does not delete or
  modify the latest successful report.
- PostgreSQL migrations must enforce foreign keys and unique constraints. The
  database must hold at most one current `latest_report` record.

### Domain Types

### SprintReport

- `sprintId`
- `sprintName`
- `sprintStartDate`
- `sprintEndDate`
- `dataTimestamp`
- `projectKey`
- `boardId`
- `totalIssueCount`
- `completedIssueCount`
- `remainingIssueCount`
- `completionPercentage`
- `totalStoryPoints`
- `completedStoryPoints`
- `remainingStoryPoints`
- `storyPointCompletionPercentage`
- `statusCounts`
- `statusCategoryCounts`
- `completedIssues`
- `highlightedBlockers`
- `executiveSummary`

### SprintIssue

- `issueKey`
- `summary`
- `status`
- `statusCategory`
- `assigneeName`
- `issueType`
- `storyPoints`
- `lastUpdated`
- `jiraUrl`
- `isCompleted`
- `isBlocked`

`null` or unavailable values must remain distinguishable from valid numeric
zero values.

## 12. Report Structure

1. Report title
2. Exact Jira data refresh timestamp
3. Sprint name and date range
4. Project and board identity
5. Executive summary
6. Status breakdown
7. Work-completion metrics
8. Story-point progress
9. Completed accomplishments
10. Highlighted blockers and risks
11. Direct Jira links
12. Explicit unavailable-data and missing-data notices

## 13. Non-Functional Requirements

### NFR-001: Performance

- Normal refresh must complete in under five minutes.
- Jira API calls must use pagination.
- Jira requests must have bounded retries and timeouts.
- Retry policy must not turn a permanently failed operation into an indefinite
  wait.

### NFR-002: Security

- API traffic must use HTTPS.
- Credentials must remain outside source control.
- Logs must not contain tokens or authorization headers.
- External Jira text must be escaped according to its output context.
- Assignee names must be included only when permitted.
- Local generated HTML must contain no credentials or secret configuration.

### NFR-003: Reliability

- Complete required Jira responses before generation.
- Preserve the last successful report after a failure.
- Use no partial or invalid Jira response for metrics.
- Unit tests must not require live Atlassian credentials.

### NFR-004: Maintainability

- Separate Jira retrieval, normalization, metrics, and rendering.
- Keep field mappings and completion rules configurable.
- Keep the blocker status and age threshold configurable.
- Keep no secret values in report or frontend configuration.

### NFR-005: Usability and Accessibility

- Use semantic HTML and clear labels.
- Preserve responsive behavior.
- Make unavailable and error states explicit.
- Ensure keyboard access if a React UI is provided.
- Use clear status and error feedback without exposing internal details.

### NFR-006: Deployability

- Frontend and backend must build independently.
- Docker Compose must provide repeatable local service startup.
- PostgreSQL must use the specified 15.x major version.
- Node.js must use v26.13.1.
- npm must use 11.20.0.

## 14. Configuration Contract

Configuration may be supplied by environment variables or a JSON file, but
environment variables must take precedence for secrets.

Example non-secret shape:

```json
{
  "jiraBaseUrl": "https://anitharanip.atlassian.net",
  "projectKey": "SAM1",
  "boardId": 0,
  "storyPointFieldId": "customfield_10000",
  "blockedStatus": "Blocked",
  "blockerAgeThresholdDays": 5,
  "outputPath": "C:\\workspace\\hello-genai\\current-sprint-status.html",
  "includeAssigneeNames": true
}
```

The example board ID and story-point field ID are placeholders and must be
replaced by confirmed configuration.

Environment variables must include names for:

- Jira account email
- Jira API token
- Database connection settings
- External integration controls

## 15. Testing Strategy

### Unit Tests

- Jira board, sprint, and issue response normalization
- Active-sprint ambiguity handling
- `Done` status category completion
- Issue completion percentage
- Missing issue totals
- Story-point totals and unavailable calculations
- Missing, invalid, and negative story-point values
- Exactly five-day and older blocker thresholds
- Status and status-category aggregation
- HTML and React text escaping
- Atomic report write behavior
- Credential and secret redaction

### Integration Tests

- Jira authentication
- Board lookup
- Active-sprint lookup
- Paginated issue retrieval
- Story-point field discovery or mapping
- Scheduled and manual refresh entry points
- Standalone HTML generation
- PostgreSQL persistence integration where data is persisted
- Docker Compose startup

Integration tests must use fixtures or isolated Atlassian test workspaces.
They must not mutate production Jira or Confluence data.

### Acceptance Tests

The feature is accepted when:

1. A configured active sprint produces a report in under five minutes.
2. Only issues from the configured active sprint appear.
3. Jira `Done` status categories count as complete.
4. The report includes status breakdown and issue completion.
5. The report calculates story-point progress or marks it unavailable.
6. Completed issues and their direct Jira links appear.
7. A `Blocked` issue exactly five days old is highlighted.
8. A more recent blocked issue is not highlighted.
9. Missing story points are not treated as zero.
10. Missing sprint data is clearly marked unavailable.
11. A board, sprint, authentication, or API failure leaves the previous report
    unchanged.
12. HTML output contains no credentials or authorization headers.
13. No Jira issue is edited and no external publication occurs.
14. A manager can execute the report manually.
15. A Windows scheduled task can execute the report daily.

## 16. Implementation Plan

### Phase 1: Foundation

- Add validated environment and application configuration.
- Add Docker Compose services and PostgreSQL configuration.
- Create Express integration and HTTP boundaries.
- Create shared TypeScript or JavaScript domain contracts.

### Phase 2: Jira Integration

- Implement authenticated Jira API access.
- Implement board and active-sprint resolution.
- Implement paginated issue retrieval.
- Implement response normalization and validation.

### Phase 3: Metrics and Report

- Implement status and completion calculations.
- Implement story-point availability rules.
- Implement accomplishment and blocker extraction.
- Implement atomic standalone HTML generation.

### Phase 4: Execution and Interface

- Add manual CLI or service refresh entry point.
- Add Windows scheduled-task instructions or scripts.
- Add a React/Vite review interface only if required for the approved MVP.
- Add configuration status and failure feedback.

### Phase 5: Verification

- Add unit and integration tests.
- Validate report content with Jira fixtures.
- Test failure recovery and report preservation.
- Perform manual report review.
- Verify Docker and dependency versions.

## 17. Open Questions

Before implementation begins, confirm:

1. The numeric Jira board ID.
2. The Jira project key; `SAM1` is currently a candidate.
3. The Jira story-point custom field ID.
4. Whether Jira `Done` status category is the final completion rule.
5. How to handle more than one active sprint for the board.
6. Whether assignee names may be included in the report.
7. Whether a React UI is required for the MVP or whether local CLI and HTML
   output are sufficient.
8. Whether PostgreSQL stores configuration, run history, or no MVP state.

Unresolved answers must not be guessed or replaced with default production
values.

## 18. Requirements Traceability

| Specification section | Source requirement |
|---|---|
| Active-sprint resolution | Project spec FR-1; requirements Section 5 |
| Executive summary | Project spec FR-2 |
| Status breakdown | Project spec FR-3 |
| Work completion | Project spec FR-4 |
| Story-point progress | Project spec FR-5 |
| Completed accomplishments | Project spec FR-6 |
| Blocker detection | Project spec FR-7 |
| Standalone HTML | Project spec FR-8 |
| Missing data | Project spec FR-9; requirements Section 4 |
| Manual and daily execution | Project spec FR-10 |
| Human approval | Project spec FR-11 |
| Failure handling | Project spec FR-12 |
| Security and reliability | Project spec NFR-1 through NFR-4 |
| Constitution compliance | [constitution.md](constitution.md) |

## 19. Acceptance Summary

The feature is complete when it:

1. Uses the configured Jira board and active sprint.
2. Generates a standalone HTML draft with accurate Jira-derived metrics.
3. Clearly labels missing and unavailable values.
4. Supports manual and daily scheduled execution.
5. Keeps credentials and secrets out of source control and output.
6. Preserves the previous report on failure.
7. Requires human review before external distribution.
8. Does not edit Jira or publish to Confluence.
9. Meets the technology, folder, naming, testing, and quality gates in the
   constitution.
