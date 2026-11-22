# Project Tasks

## Phase 1: Configure Jira

- [x] Review the project setup notes and identify configured values and missing Jira prerequisites.
- [x] Confirm project key `SAM1` and record Scrum board ID `1`.
- [ ] Find the full story-point field ID in Jira (format `customfield_<digits>`).
- [ ] Create and complete local `config.json`, then set the Jira API token in the configured environment variable.

## Phase 2: Generate and Review the Report

- [x] Implement the report generator and offline unit tests for calculations, pagination, blockers, and HTML escaping.
- [ ] Run the report with Jira and review the generated HTML against the active sprint.

## Phase 3: Schedule Daily Refresh

- [ ] After a successful manual run, install and verify the Windows daily scheduled task.

## Progress Notes

- The project key `SAM1` and board ID `1` were confirmed. The supplied story-point field value `12` is not a valid configured Jira field ID; the user deferred looking up its full `customfield_<digits>` ID.
- Live Jira configuration and validation remain blocked until the story-point field ID is known and account-specific configuration/token details are available. No incomplete `config.json` was created.
- The report is a local draft only; a person must review it before manual sharing. When resuming, start with the first unchecked task and update this file as work progresses.
