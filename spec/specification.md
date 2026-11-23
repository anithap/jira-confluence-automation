# Feature Specification: Jira Sprint Status Automation

**Project:** Jira/Confluence Automation
**Feature:** Daily Jira Active-Sprint Status Report
**Status:** Clarified
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
- Expose a React/Vite review application or Express REST API in the prototype.
- Persist application state in PostgreSQL in the prototype.
- Integrate with Confluence or publish, update, or synchronize any Confluence
  page.
- Implement dashboard login, Jira OAuth, multi-user authorization, or external
  network access.

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

- Prototype runtime: Python 3.11 or the repository's installed supported Python
  version
- Primary interface: command-line script
- Report format: standalone HTML
- Atlassian integration: Jira Cloud REST API
- Scheduling: local Windows Scheduled Task
- Database: none for the prototype
- Docker: not required for prototype execution
- Confluence: out of scope
- Future architecture in [constitution.md](constitution.md): React 18/Vite,
  Node.js v26.13.1/Express, PostgreSQL 15.x, and Docker 29.9.3

Python package manifests or lock files must pin supporting dependencies. The
MVP is independent of PostgreSQL, React/Vite, Express, Docker, and Node.js.
The constitution defines the architecture for a future web application phase.

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

Resolution rules:

- Zero active sprints: fail with `NO_ACTIVE_SPRINT`.
- Exactly one active sprint: continue.
- More than one active sprint: fail with `AMBIGUOUS_ACTIVE_SPRINT`.
- Closed, future, and archived sprints are not active candidates.
- Sprint and issue data must correspond to the same board and project.

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

Use this deterministic template:

```text
Sprint: <sprint name> (<start date> to <end date>)
Issues: <completed> completed, <remaining> remaining, <total> total
Issue completion: <percentage>% or Unavailable
Story points: <completed>/<total> completed or Unavailable
Highlighted blockers: <count>
Data: refreshed at <UTC timestamp> (<local timezone>)
Status: Draft - review before distribution
```

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

Use Jira's `Done` status category only. Status-name allowlists and overrides
are out of scope for the prototype.

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

Rules:

- Valid story points are finite numeric values greater than or equal to zero.
- Zero is valid.
- Missing Jira values, null values, invalid strings, and negative values mark
  the story-point calculation unavailable.
- `totalStoryPoints`, `completedStoryPoints`, and `remainingStoryPoints` are
  each `null` when an accurate calculation is impossible.
- The percentage is `completedStoryPoints / totalStoryPoints`, rounded to two
  decimal places for display.
- The calculation uses current active-sprint scope, not a historical initial
  scope or a manually inferred burnup.
- No historical or projected chart is generated.

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

The HTML file must be UTF-8 encoded and use a standalone `.html` extension.
Jira issue links must open in a new browser tab or window. The prototype must
not include a download API or iframe preview. A report is stale if it is more
than 24 hours after its `dataTimestamp`; stale reports must display a clear
warning and preserve the timestamp.

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

Scheduling decisions:

- The Windows Scheduled Task uses one configured local timezone.
- The task starts once at the user-selected local time.
- A failed run emits an error and does not retry automatically.
- Scheduled and manual runs must not run concurrently. If the process detects
  an existing run lock, it exits non-zero without changing the report.
- Missed executions due to a stopped machine or disabled task are not run
  automatically after startup.

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

Express REST endpoints and a React/Vite frontend are **out of scope** for the
prototype. The prototype interface is the command line and the output is the
standalone HTML file.

The prototype CLI contract is:

```text
python generate_sprint_report.py --config config.json
```

Exit status `0` means the report was generated and atomically replaced. A
non-zero exit means generation failed and the previous report must remain
unchanged. Standard output and error output must contain no Jira credential or
authorization header.

## 10. UI Screens

React/Vite UI screens are **out of scope** for the prototype. The HTML report
is the complete user-facing deliverable. It must be opened directly in a
browser, remain clearly labeled as a human-review draft, and provide no
automatic distribution controls.

## 11. Data Model

PostgreSQL persistence is **out of scope** for the prototype. The application
stores no run history or report snapshot in a database. The latest successful
HTML file is the only retained report artifact.

The prototype's transient in-memory data model is:

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
- A React UI is out of scope; the standalone HTML must remain responsive and
  keyboard-independent for direct browser use.
- Use clear status and error feedback without exposing internal details.

### NFR-006: Deployability

- The prototype must run locally on Windows without Docker.
- Docker, React/Vite, Express, PostgreSQL, Node.js, and npm requirements in the
  constitution apply to future application phases, not the prototype.
- The prototype may use Python 3.11 or the repository-supported interpreter.
- Supporting packages must be declared in `requirements.txt` or a lock file.

## 14. Configuration Contract

Configuration may be supplied by environment variables or a JSON file, but
environment variables must take precedence for secrets.

Environment variables:

| Variable | Purpose |
|---|---|
| `JIRA_BASE_URL` | Jira Cloud base URL |
| `JIRA_ACCOUNT_EMAIL` | Jira account email |
| `JIRA_API_TOKEN` | Jira API token |
| `JIRA_PROJECT_KEY` | Jira project key |
| `JIRA_BOARD_ID` | Jira numeric board ID |
| `JIRA_STORY_POINT_FIELD_ID` | Jira story-point custom field ID |
| `JIRA_BLOCKED_STATUS` | Optional blocker status name; default `Blocked` |
| `JIRA_BLOCKER_AGE_DAYS` | Optional age threshold; default `5` |
| `REPORT_OUTPUT_PATH` | Standalone HTML destination |
| `INCLUDE_ASSIGNEE_NAMES` | Optional `true`/`false`; default `true` |

The JSON file is the only non-secret configuration source for its keys.
Environment variables override matching JSON keys. Secrets must never be read
from or written to the JSON file.

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

For matching JSON keys, use these names:

| JSON key | Type | Required |
|---|---|---|
| `jiraBaseUrl` | string | Yes |
| `jiraAccountEmail` | string | Yes |
| `projectKey` | string | Yes |
| `boardId` | integer | Yes |
| `storyPointFieldId` | string | Yes |
| `blockedStatus` | string | No; default `Blocked` |
| `blockerAgeThresholdDays` | integer | No; default `5` |
| `outputPath` | string | Yes |
| `includeAssigneeNames` | boolean | No; default `true` |

The Jira API token is accepted only through `JIRA_API_TOKEN`. Unknown JSON
keys are rejected. Invalid types, negative age thresholds, malformed URLs,
empty required strings, and missing secrets are fatal validation errors.

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
- HTML text escaping
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
- Atomic output replacement

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

- Add validated environment and JSON configuration.
- Create the Python CLI entry point and Jira integration boundaries.
- Add fixture-based unit-test support.

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

- Add the manual CLI refresh entry point.
- Add Windows scheduled-task instructions or scripts.
- Keep the React/Vite review interface out of scope.
- Keep report refresh and run state local to CLI process output.

### Phase 5: Verification

- Add unit and integration tests.
- Validate report content with Jira fixtures.
- Test failure recovery and report preservation.
- Perform manual report review.
- Verify Windows scheduling and Python/dependency versions.

## 17. Open Questions

There are no unresolved MVP scope questions. Confirmed or decided prototype
values are:

1. The MVP is a Python CLI with standalone HTML output.
2. Confluence, React/Vite, Express, PostgreSQL, Docker, OAuth, and a web UI are
   out of scope.
3. Jira's `Done` status category defines completed work.
4. A `Blocked` status name defines blockers by default, with the status name
   configurable.
5. Missing or invalid story points make story-point totals unavailable.
6. The previous HTML report is retained after failed refreshes.
7. Board ID, project key, account email, and story-point field ID remain
   deployment configuration prerequisites.

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
