# Jira Sprint Status Automation — Implementation Backlog

Priority: unblock Jira setup and complete a live end-to-end report first. The requested phase order is retained. Checked items reflect implementation verified in the current workspace.

## Setup

- [x] Confirm the target Jira project key is `SAM1` and the selected Scrum board ID is `1`.
- [ ] **P0 — Identify the story-point custom field:** inspect Jira field metadata, confirm the field is available on sprint issues, and record its full ID in `customfield_<digits>` format. The previously supplied value `12` is not a valid configured field ID.
- [ ] **P0 — Prepare local configuration:** copy `config.example.json` to an untracked `config.json`; set the confirmed Jira URL, project, board, account email, story-point field, blocker rule, and output path; run configuration validation.
- [ ] **P0 — Configure the Jira secret:** set the API token in the configured environment variable for the Windows account that will run the report; verify it is available without putting the token in a file, command history, logs, or report.
- [ ] Confirm the selected board is the intended project board and whether exactly one active sprint is the expected operating condition; retain the explicit error behavior for zero or multiple active sprints.

## Core Features

- [x] Validate required configuration, HTTPS Jira URL, board ID, token-variable name, story-point field ID, and blocker settings.
- [x] Authenticate to Jira Cloud and retrieve the configured board, exactly one active sprint, and all sprint issue pages with bounded retries.
- [x] Normalize issue fields and restrict report calculations to the configured project.
- [x] Calculate status counts, Done-category completion, story-point totals, missing estimates, and configurable stale-blocker highlights without treating missing values as zero.
- [ ] Add an explicit configuration option for displaying assignee names; honor it throughout the report and document a team-approved default.
- [ ] Confirm whether the team requires a configurable completion-status allowlist; if so, add validation and tests, otherwise document the Jira `Done` category as the completion rule.
- [x] Render a standalone responsive HTML draft with a data timestamp, summary, progress, accomplishments, blockers, and escaped Jira text.
- [x] Write the report atomically only after successful retrieval and rendering, preserving the previous report on failure.
- [x] Provide a Windows Task Scheduler installer for a user-selected daily local run.

## Integration

- [ ] **P0 — Run the configured CLI against Jira:** execute `python generate_sprint_report.py --config config.json` and resolve authentication, permission, board, sprint, or field errors.
- [ ] Verify the returned sprint is the intended active sprint and that report issue keys, statuses, assignees, estimates, and links correspond to Jira.
- [ ] Confirm the Jira API returns all pages and that only issues from the intended project appear in the report.
- [ ] Verify the displayed refresh timestamp represents the successful Jira data refresh, and that a failed scheduled refresh leaves the previous report and its last-success timestamp intact.
- [ ] Confirm a successful manual run writes the configured HTML output, then install the daily task with `.\install_daily_task.ps1`.
- [ ] Run the scheduled task under the intended Windows account and verify its last run succeeds at the selected local time.

## Testing

- [x] Add offline tests covering status and point calculations, missing estimates, empty sprints, the five-day blocker boundary, status aggregation, issue pagination, project filtering, and HTML escaping.
- [ ] Add focused tests for invalid and missing configuration, missing token, malformed Jira responses, authentication/API failures, bounded retry behavior, and invalid or negative story-point values.
- [ ] Add regression tests that verify incomplete Jira retrieval or report-write failure leaves an existing output file unchanged.
- [ ] Run `python -m unittest discover -s tests -v` and resolve any failures.
- [ ] Perform acceptance validation against the configured Jira board: complete report in under five minutes, required report sections present, missing sprint dates shown as unavailable, no credentials in logs or output, no Jira edits, and no automatic distribution.

## Documentation

- [x] Document manual setup, token environment-variable handling, report generation, scheduled-task installation, report rules, and offline tests in `README.md`.
- [x] Provide a report template, completion instructions, and a fictional example under `reports/`.
- [ ] After identifying the story-point field, document how to set it in local configuration without publishing account-specific secrets.
- [ ] Update the README with any live-validation or scheduled-task setup findings that change the operator workflow; preserve the human-review-before-sharing requirement.

## Handoff Notes

- The next action is to look up the Jira story-point field ID. The user deferred this lookup; do not guess an ID or create a knowingly invalid `config.json`.
- At the start of a new session, read `project_spec.md` for requirements and this file for current progress; continue with the first unchecked P0 task.
- Keep API tokens and other secrets out of this backlog and all generated reports.

## Decisions Made

- 2026-11-23: Use project key `SAM1` and Jira Scrum board ID `1` for the target configuration.
- 2026-11-23: Generate a deterministic local HTML draft from Jira data; require human review and do not edit Jira or distribute reports automatically.
- 2026-11-23: Treat Jira's `Done` status category as complete; highlight blockers using the configured blocked status and last-updated age threshold (default five days).
- 2026-11-23: Read the Jira API token from an environment variable, not from `config.json`; do not retain historical sprint snapshots.
