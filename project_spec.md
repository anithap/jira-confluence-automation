# Technical Specification: Weekly Jira Sprint Status Automation

## 1. Overview

Build a manual automation for a Manager responsible for a 10-person Development and Support team. The automation reads the team's active Jira sprint and generates a standalone local HTML report for delivery-health, blocker, and stakeholder-status review.

The initial implementation prioritizes accurate, deterministic reporting. Jira data is normalized and presented according to fixed, configurable rules. Generative AI is not required.

## 2. Goals

- Generate a current-sprint status report in under five minutes.
- Show delivery progress, status distribution, completed work, story-point totals, and blocked work.
- Require human review before the report is shared.
- Keep credentials outside source control.
- Avoid Jira edits and external report distribution.

## 3. Users and Roles

| Role | Responsibility |
|---|---|
| Manager | Runs or requests the report, reviews it, and distributes it manually |
| Development and Support team | Maintains Jira status and blocker information |
| Stakeholders | Consume only the manually approved report |

Assignee names and Jira issue links may be included in the report.

## 4. Source Systems

### Jira

- **Deployment:** Jira Cloud
- **Base URL:** `https://anitharanip.atlassian.net`
- **Candidate project key:** `SAM1`
- **Board:** Single configured Scrum board
- **Board ID:** Not yet supplied
- **Sprint:** Active sprint for the configured board
- **Authentication:** Jira API token
- **Account email:** `anitharani.p@gmail.com`
- **Story-point field:** Unknown; discover from Jira metadata or configure explicitly

Expected issue fields:

- Issue key
- Summary
- Status
- Status category
- Assignee
- Story points
- Last updated time
- Issue type
- Sprint
- Jira web link

### Report Destination

- **Interface:** Command-line script
- **Output:** `C:\workspace\hello-genai\current-sprint-status.html`
- **Format:** Standalone HTML
- **Delivery:** Local file opened manually

## 4.1 Data Refresh Frequency

- **Required refresh frequency:** Daily.
- The automation must refresh Jira sprint data at least once per calendar day.
- A generated report must include a data timestamp showing the exact Jira data refresh time.
- Historical Jira snapshots are not required for the initial release.
- Manual execution must remain available so the report can be refreshed outside the daily run.
- An automated daily scheduled task is the preferred implementation for routine refreshes.
- The scheduled task must preserve the existing report and emit an error if a refresh fails.
- The report must not present stale data without clearly showing the last successful refresh timestamp.

## 5. Functional Requirements

### FR-1: Resolve the Active Sprint

The automation must:

1. Load configuration and the Jira API token from environment variables.
2. Authenticate to Jira Cloud.
3. Retrieve the configured Scrum board.
4. Resolve the board's active sprint.
5. Retrieve all issues in the active sprint using pagination.
6. Stop with a clear error if board, sprint, authentication, or Jira API access is unavailable.

The board ID must be supplied or discovered before execution.

### FR-2: Generate the Executive Summary

The report must include a concise deterministic summary containing:

- Sprint name and date range
- Data timestamp
- Project and board identifiers
- Completed work
- Remaining work
- Sprint blockers
- Stakeholder-facing status narrative

The summary must use only values calculated from Jira data.

### FR-3: Show Status Breakdown

The report must display issue counts by Jira status and status category.

- Counts must reflect issues in the active sprint only.
- A status breakdown must be visible even when story points are missing.
- Status names and categories must be sourced directly from Jira.

### FR-4: Calculate Work Completion

An issue is complete when its Jira status belongs to the `Done` status category.

The report must calculate:

- Total current-sprint issue count
- Completed issue count
- Remaining issue count
- Completion percentage based on issue count

The percentage formula is:

```text
completed issue count / total issue count
```

The completion definition must be configurable if the team later requires an explicit status allowlist.

### FR-5: Calculate Story-Point Progress

The automation must calculate:

- Total story points in the active sprint
- Completed story points
- Remaining story points
- Completed story-point percentage

The Jira story-point custom field must be identified before calculations are enabled.

Missing story-point values must be explicitly reported as missing; they must not be treated as zero. Totals must be marked unavailable if missing values prevent an accurate calculation.

### FR-6: List Completed Accomplishments

The report must list completed issues in the active sprint.

Each accomplishment should include:

- Issue key
- Summary
- Assignee, if available
- Jira issue link

The report must not infer accomplishments from stale or partial Jira data.

### FR-7: Identify Blockers and Risks

An issue is a blocker when its status is exactly `Blocked`.

The issue must also have a last-updated timestamp at least five days old to appear in the highlighted blocker list.

The report must include:

- Issue key
- Summary
- Assignee
- Current status
- Last updated time
- Jira issue link

If no blocker meets the rule, the report must state that no blocker is highlighted.

Last update is an age signal only; it does not establish when the issue first became blocked.

### FR-8: Render Standalone HTML

The report must:

- Open directly in a browser without a server
- Use responsive desktop and mobile styling
- Include clear labels and source values
- Include direct Jira issue links
- Escape all external Jira text
- Contain no API credentials or authorization headers

### FR-9: Missing Data

Missing data must be clearly marked as unavailable.

The automation must not:

- Substitute guessed story-point values
- Invent missing sprint dates
- Estimate blocker history that Jira does not provide
- Present a partial report as complete

### FR-10: Daily and Manual Execution

The automation must support both a daily local Windows scheduled task and
manual command-line execution:

```text
python generate_sprint_report.py --config config.json
```

Configuration must include:

- Jira base URL
- Board ID
- Project key
- API token environment-variable name
- Story-point field ID
- Blocked status
- Blocker age threshold
- Output path

The token must be read from an environment variable or local secret store.
The daily task must run at a user-selected local time. Manual execution must
remain available independently of the scheduled task.

### FR-11: Human Approval

The automation must produce only a local draft.

It must not:

- Email the report
- Publish it to Jira
- Post it to Teams or Slack
- Automatically distribute it

The Manager must review the report before any manual sharing.

### FR-12: Failure Handling

If Jira is unavailable, authentication fails, configuration is invalid, the board or sprint cannot be resolved, or Jira returns incomplete required data:

1. Stop report generation.
2. Print a concise error describing the failed operation.
3. Do not overwrite the previous report.
4. Do not fabricate missing metrics.

## 6. Non-Functional Requirements

### NFR-1: Performance

- Normal report generation must complete in under five minutes.
- Jira API calls must use pagination.
- Jira requests must be bounded and retried only with a bounded retry policy.

### NFR-2: Security

- Jira API tokens must remain outside source control.
- Browser output must contain no credentials or secret values.
- API traffic must use HTTPS.
- External Jira text must be HTML-escaped.
- Assignee names may be included only as configured.

### NFR-3: Reliability

- A successful Jira response must be complete before the report is generated.
- The prior report must remain unchanged after an error.
- Transient Jira failures may trigger bounded retries.
- Unit tests must not require live Jira credentials.

### NFR-4: Maintainability

- Jira retrieval must be isolated from calculation and rendering.
- Story-point field IDs and status mappings must be configuration values.
- Blocker thresholds must be configurable.
- Output rendering must not include secret configuration.

## 7. Architecture

```text
Command Line
    |
    v
Configuration and Secrets
    |
    v
Jira API Client
    |
    v
Sprint and Issue Normalizer
    |
    v
Deterministic Metrics Engine
    |
    v
HTML Report Renderer
    |
    v
Local HTML Draft
```

### Components

- **Configuration loader:** reads JSON configuration and environment variables.
- **Jira API client:** handles authentication, pagination, retries, and API errors.
- **Sprint normalizer:** validates Jira responses and maps statuses and custom fields.
- **Metrics engine:** calculates issue totals, completion, story-point totals, and blockers.
- **HTML renderer:** escapes Jira text and generates a standalone report.

## 8. Data Model

```text
SprintReport
- sprintName
- sprintStartDate
- sprintEndDate
- dataTimestamp
- projectKey
- boardId
- totalIssueCount
- completedIssueCount
- remainingIssueCount
- completionPercentage
- totalStoryPoints
- completedStoryPoints
- remainingStoryPoints
- storyPointCompletionPercentage
- statusCounts[]
- completedIssues[]
- highlightedBlockers[]
- executiveSummary[]

SprintIssue
- issueKey
- summary
- status
- statusCategory
- assigneeName
- issueType
- storyPoints
- lastUpdated
- jiraUrl
- isCompleted
- isBlocked
```

## 9. Report Structure

1. Report title and generation timestamp
2. Sprint identity
3. Executive summary
4. Work-status breakdown
5. Work-completion metrics
6. Story-point progress
7. Completed accomplishments
8. Highlighted blockers and risks
9. Direct Jira links

## 10. Testing Strategy

### Unit Tests

- Jira response normalization
- Done-status classification
- Issue completion percentage
- Story-point calculations
- Missing story-point handling
- Five-day blocker threshold
- Status breakdown aggregation
- HTML escaping
- Failure behavior

### Integration Tests

- Jira authentication
- Board lookup
- Active-sprint lookup
- Paginated issue retrieval
- Story-point field discovery
- Standalone HTML generation

### Acceptance Tests

- A configured active sprint produces a report in under five minutes.
- Only issues in the active sprint appear in the report.
- Jira `Done` statuses count as complete.
- The report includes status breakdown, work completion, story points, accomplishments, and blockers.
- The Windows scheduled task supports a daily run at a user-selected local time.
- A `Blocked` issue updated at least five days ago appears in the blocker list.
- Missing story points are identified and are not counted as zero.
- No credentials appear in logs or output.
- A failed Jira request leaves the previous report unchanged.
- No Jira issue is edited or externally distributed.

## 11. Implementation Plan

### Phase 1: Configuration and Jira Access

- Add configuration validation.
- Implement API-token loading.
- Implement board, active-sprint, and issue retrieval.
- Implement pagination and bounded retries.

### Phase 2: Metrics and Rendering

- Implement status and story-point calculations.
- Implement blocker detection.
- Implement accomplishment extraction.
- Generate the standalone HTML report.

### Phase 3: Validation

- Add unit and integration tests.
- Validate the report against Jira fixtures.
- Perform a manual review of the local HTML output.

## 12. Open Decisions

1. Numeric Jira board ID.
2. Jira story-point custom field ID.
3. Whether `SAM1` is the final project key.
4. Whether a single active sprint is always guaranteed.

## 13. Explicitly Out of Scope

- Jira issue editing
- Automatic Jira updates
- Email, Teams, Slack, or Jira distribution
- Interactive web dashboard
- Hosted scheduled execution
- Historical sprint reporting
- Multiple boards or projects
- Assignee workload reporting
- Next-week priorities
- Confluence integration
- Generative AI narratives
- Automated publishing or approval

## 14. Acceptance Criteria

The implementation is accepted when:

1. A Manager can run the command manually.
2. It authenticates to `https://anitharanip.atlassian.net`.
3. It reads the configured project and active sprint.
4. It generates `C:\workspace\hello-genai\current-sprint-status.html`.
5. It includes executive summary, status breakdown, work completion, story points, accomplishments, and blockers.
6. It highlights only blockers in `Blocked` status that were last updated five or more days ago.
7. It clearly marks missing or unavailable data.
8. It makes no Jira changes.
9. It requires manual review before distribution.
10. It fails clearly and preserves the previous report when Jira data is unavailable.
