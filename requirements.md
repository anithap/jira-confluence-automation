# Requirements: Daily Jira Sprint Status Report

## 1. Purpose and users

Generate a reliable current-sprint report for a Manager overseeing a 10-person
Development and Support team. The report supports delivery-health, blocker, and
stakeholder-status decisions.

## 2. Scope and delivery

- Read one active sprint from one configured Jira Cloud Scrum board.
- Use Jira site `https://anitharanip.atlassian.net` and project key `SAM1`
  (candidate; confirm against the selected board).
- Generate a standalone HTML report at the configured output path, defaulting
  to `C:\workspace\hello-genai\current-sprint-status.html`.
- Refresh data daily through a local Windows scheduled task, while retaining
  manual command-line execution.
- Include a data timestamp. Do not retain historical snapshots.
- The report is a local draft. The Manager must review it before manually
  sharing it.

## 3. Report content

The report must include:

1. Sprint name, date range, project, board, and data timestamp.
2. A deterministic executive summary based only on Jira data.
3. Issue counts grouped by Jira status and status category.
4. Completed, remaining, and total issue counts, plus completion percentage.
5. Total, completed, and remaining story points, plus story-point completion
   percentage when the values and denominator are available.
6. Completed issue accomplishments with issue key, summary, assignee when
   available, and Jira link.
7. Highlighted blockers with issue key, summary, assignee, status, last-updated
   timestamp, and Jira link.

## 4. Calculation rules

- An issue is complete when its Jira status category is `Done`.
- Issue completion percentage is completed issue count divided by total issue
  count. If there are no issues, show the percentage as unavailable.
- Story-point values come from a configured Jira custom field. Do not treat
  missing, invalid, or negative values as zero. Mark affected totals and
  percentages unavailable when they cannot be calculated accurately.
- A blocker must have status exactly `Blocked` (case-insensitive comparison)
  and a Jira last-updated timestamp at least five days old.
- Last update is only an age signal; it does not establish when the issue
  became blocked.

## 5. Jira integration and configuration

- Authenticate to Jira Cloud with an API token and account email.
- Read the API token from an environment variable; never store it in source
  control, logs, or generated HTML.
- Configure Jira base URL, board ID, project key, token environment-variable
  name, story-point field ID, blocker status and age threshold, and output path.
- Retrieve the board's active sprint and all sprint issues with pagination.
- Reject ambiguous active-sprint results rather than selecting one arbitrarily.
- The board ID and story-point custom field ID remain configuration prerequisites.

## 6. Reliability and security

- Use HTTPS for Jira requests and bounded retries for transient failures.
- Generate a report only after all required Jira responses have succeeded.
- On refresh failure, report a clear error and leave the previous HTML report
  unchanged.
- Escape Jira-supplied text before rendering HTML.
- Do not edit Jira, email the report, or automatically publish or distribute it.
- Keep manual report generation available even when a daily task is configured.

## 7. Acceptance criteria

- The command-line report can be run with a JSON configuration and API token
  environment variable.
- The daily Windows task runs at a user-selected local time.
- The report includes all content in Section 3 and uses the rules in Section 4.
- The status breakdown reports actual Jira status counts, not only broad
  categories.
- Missing story points and unavailable calculations are explicitly labeled.
- A `Blocked` issue last updated exactly five days ago is highlighted.
- HTML output contains no credentials and escapes external Jira text.
- A Jira or configuration failure leaves an existing report unchanged.
- Unit tests run without Jira credentials.
