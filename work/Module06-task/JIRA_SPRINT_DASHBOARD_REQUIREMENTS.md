# Jira Sprint Progress Dashboard - Requirements Document

## 1. Purpose

Build an interactive dashboard that gives an engineering manager a clear view of one team's current Jira sprint progress.

The dashboard must help the manager understand:

- The distribution of work by Jira status.
- How much of the sprint work is complete.
- How story points are being completed over the sprint.

## 2. Users and Goals

- **Primary audience:** Engineering manager.
- **Team scope:** One team.
- **Primary decision supported:** Delivery progress and sprint health.
- **Secondary decisions:** Identifying where active work and remaining work are concentrated.

## 3. Scope

### In scope

- Jira Cloud integration.
- One Jira project and one Scrum board.
- The current or active sprint only.
- Live Jira API data.
- A standalone web application.
- Desktop-first presentation with responsive behavior.
- Manual data refresh.

### Out of scope for the initial version

- Multiple teams or projects.
- A portfolio or aggregated cross-team view.
- Historical sprint comparison.
- Burndown charts.
- Issue-count burnup.
- Blocker views.
- Assignee workload.
- Sprint-goal tracking.
- Cycle-time reporting.
- Velocity reporting.
- Defect-specific reporting.
- Automatic polling or scheduled refresh.

## 4. Source System

- **Jira deployment:** Jira Cloud.
- **Jira site:** `https://anitharanip.atlassian.net`
- **Project key candidate:** `SAM1`
- **Issue used to identify the project:** `SAM1-8`
- **Board:** Not yet confirmed.
- **Board ID:** Must be supplied or discovered through the Jira API.

The personal Jira URL initially provided identifies the user's worked-on items, not a board, and must not be used as a board configuration value.

## 5. Authentication and Security

- **Prototype authentication:** Jira Cloud API token.
- **Account email:** `anitharani.p@gmail.com`
- Store the API token in an environment variable or local secret store.
- Do not place the token in source control or browser code.
- Use HTTPS for Jira API traffic.
- OAuth may be considered later if the dashboard is extended to authenticated multi-user use.

## 6. Delivery and Technology

- **Interface:** Standalone web application.
- **Recommended stack:** React/TypeScript for the frontend and a small backend for Jira API access.
- **Primary viewport:** Desktop/laptop.
- **Visual style:** Clean Jira-style, with compact views and familiar status colors.
- The final framework may use existing organization standards if an existing application or framework is specified later.

## 7. Dashboard Requirements

### 7.1 Status Breakdown

The dashboard must show how current-sprint issues are distributed across their Jira statuses.

- Each status or Jira status category must have a visible count.
- The display should distinguish completed work from work not yet complete.
- The exact status mapping must be configurable.

### 7.2 Work Completion

The dashboard must show current-sprint work completion.

The initial implementation should present:

- Completed work.
- Remaining work.
- Completion percentage.
- Total story points or issue count used as the denominator.

Jira's `Done` status category should be the default definition of completed work unless more specific status rules are configured.

### 7.3 Story-Point Burnup

The dashboard must include a story-point burnup chart for the current sprint.

The chart should show, as Jira data is available:

- Total current committed story points.
- Completed story points over sprint time.
- Sprint scope and the start/end boundaries.

The chart must not invent historical values. If Jira history is unavailable or the story-point field cannot be resolved, the affected value must be shown as unavailable.

## 8. Data and Refresh

- Retrieve sprint and issue data through the Jira REST API.
- Use the configured board to resolve the active sprint.
- Resolve issues belonging to that sprint.
- Paginate Jira API results.
- Refresh manually on user action.
- Do not poll automatically in the initial version.
- Preserve the previous dashboard state if data refresh fails.
- Show a clear error when the board, active sprint, or project is unavailable.

## 9. Data Definitions

The implementation must use explicit, configurable field mappings.

- **Project:** Jira project key.
- **Board:** Numeric Jira Scrum board ID.
- **Sprint:** Active sprint for the configured board.
- **Story-point field:** Jira custom field ID.
- **Completed:** Jira `Done` status category by default.
- **Issue count:** Number of Jira issues returned for the active sprint.
- **Story-point total:** Sum of configured story-point values for returned issues.

Missing story-point values must not be assumed to be zero. The dashboard must report them as missing or unavailable and explain the effect on totals.

## 10. Display Requirements

The first release should:

- Load manually with a clear refresh action.
- Identify the sprint name and date range.
- Identify the project and board.
- Display the three required metric areas:
  1. Status breakdown.
  2. Work completion.
  3. Story-point burnup.
- Use clear labels and avoid displaying raw Jira API responses.
- Preserve readable layout on smaller widths even though desktop is primary.
- Format story points consistently with whole or decimal values.

## 11. Security and Reliability

- API credentials must remain server-side or in local secret storage.
- Do not expose API tokens or authorization headers in network responses or frontend code.
- Handle Jira authentication, board lookup, sprint lookup, API pagination, and request failures clearly.
- Retain the last successful dashboard data after a refresh failure.
- Do not use partial or invalid Jira responses to calculate and display results.

## 12. Open Decisions

1. Confirm that `SAM1` is the intended Jira project key.
2. Supply or discover the numeric Jira board ID.
3. Confirm the Jira custom field ID used for story points.
4. Confirm whether Jira's `Done` status category is the final completion rule.
5. Confirm the active-sprint resolution rule if more than one sprint is active.
6. Confirm whether decimal and missing story-point values require special display rules.

## 13. Acceptance Criteria

The initial implementation is accepted when:

1. It is a usable web application in a desktop browser.
2. It connects to Jira Cloud using a token without exposing credentials.
3. It resolves the configured active sprint.
4. It displays an accurate status breakdown for sprint issues.
5. It displays work-completion totals and percentage.
6. It displays a story-point burnup chart for the current sprint.
7. It supports manual refresh.
8. It clearly labels unavailable or missing data.
9. It leaves the previous successful view intact after a failed refresh.
10. It does not support or imply out-of-scope historical or multi-team reporting.
