# Instructions for Completing the Jira Sprint Status Report

Use [template.md](template.md) to prepare a current-sprint status draft from the configured Jira board. The report is for a Manager overseeing a Development and Support team. It is a snapshot for human review, not a forecast or a historical comparison.

## 1. Get current Jira data

1. Confirm the configuration uses the intended Jira project, board ID, and story-point custom field.
2. Ensure the Jira API token is available through the configured environment variable. Never paste the token into the report, template, or instructions.
3. Generate a fresh report by running the command in the project README:

   ```powershell
   python generate_sprint_report.py --config config.json
   ```

4. The configured daily Windows task can refresh the report automatically. Manual execution is also available.
5. If the command fails, do not assemble a report from partial data or overwrite a prior successful report. Resolve the error and refresh again.

The board ID and story-point field ID must be configured before running against Jira. Verify the project key and active sprint belong to the intended team.

## 2. Complete the report header and summary

- **Data refreshed:** Copy the successful report's UTC timestamp exactly, including its timezone.
- **Project, board, sprint, and dates:** Copy these values from Jira/report output. Do not guess missing dates or identifiers; use `Unavailable` and explain the impact under Data gaps.
- **Report owner:** Enter the preparer or manager's name if appropriate.
- **Executive summary:** Write 2–4 factual sentences using the displayed metrics. Mention notable completed work, remaining work, blockers that meet the rule, and data gaps. Do not label the sprint on track/at risk or predict delivery unless a separate agreed rule supports that conclusion.

## 3. Fill in status breakdown and work completion

- Include each distinct Jira status and its Jira status category with its issue count.
- Ensure the row counts add up to the total number of issues in the active sprint.
- Count an issue as complete only when its Jira status category is `Done`.
- Calculate issue completion as:

  ```text
  completed issue count / total issue count * 100
  ```

- If the sprint has no issues, mark the percentage `Unavailable` rather than dividing by zero.
- Use the `In Progress` and `To Do` status categories for the in-progress and not-started counts. Include each issue only once.

## 4. Fill in story-point progress

- Use the configured Jira story-point field; do not substitute another estimate field without updating the configuration.
- Report total, completed, and remaining points only when their inputs are complete and valid.
- Missing, invalid, or negative point values are not zero. Identify affected issues in the missing-points line.
- If any sprint issue lacks points, mark the current-sprint total unavailable. If any completed issue lacks points, mark completed points unavailable.
- Remaining points require both total and completed points. Story-point completion is completed points divided by total points; if the total is zero or an input is unavailable, mark the percentage unavailable.
- Do not infer the original sprint commitment, scope changes, or a projected completion date.

## 5. List accomplishments and remaining work

- **Accomplishments:** Include issues whose Jira status category is `Done`. Use the issue key, a direct Jira link, the current summary, and assignee; use `Unassigned` when Jira has no assignee.
- **In-progress work:** Include issues in the `In Progress` category, retaining their exact Jira status name.
- **Not started:** Include issues in the `To Do` category.
- Keep summaries factual and concise. Do not claim an outcome that is not represented by Jira data.
- Write `None` when a section has no issues.

## 6. Identify blockers and risks

Highlight an issue only when both conditions are true:

1. Its Jira status is exactly `Blocked` (case-insensitive comparison).
2. Its Jira `updated` timestamp is at least five days before the report's data-refresh time.

Record the issue key, direct link, summary, assignee, status, and last-updated timestamp. Last update is only an age signal; it does not show when the issue first became blocked. If the timestamp is missing, do not claim the issue meets the age rule; note that the blocker could not be assessed under Data gaps.

Under Data gaps or other risks, list unavailable values and explain their effect, such as a missing story-point field preventing point totals. Do not invent a risk level or mitigation.

## 7. Review and share

1. Check that the report describes the active sprint only and that totals match the Jira results.
2. Verify issue links and assignee names, and remove any information not needed by the intended audience.
3. Mark the review status and decision at the bottom of the report.
4. Share only after a human has reviewed and approved it. The automation does not email, publish, or distribute the report.

## Example

[example.md](example.md) shows a completed report with fictional data. Its sample issue keys and links are illustrative and must not be copied as live Jira facts.
