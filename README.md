# Daily Jira Stakeholder Status Report

Generate a standalone HTML daily stakeholder draft for the single active
sprint on a configured Jira board. The report includes an executive summary,
status breakdown, work completion, story-point progress, completed-issue
accomplishments, and blockers/risks. The script reads Jira data only; it does
not edit Jira, email the report, or distribute it. Review the local HTML file
before sharing it manually.

## Setup

1. Copy `config.example.json` to `config.json`.
2. Set `board_id`, `jira_email`, the Jira story-point field ID, and the team's
   blocker status. Confirm that `blocker_status` matches Jira's actual status
   name.
3. Set the Jira API token in the environment variable named by `api_token_env`.
   Do not put the token in the JSON file.
4. Set the Jira API token as a persistent environment variable for the Windows
   account that will run the scheduled task. Do not put the token in the JSON
   file.
5. Test the report manually:

   ```powershell
   python generate_sprint_report.py --config config.json
   ```

The report is written to `output_path` only after all Jira requests succeed.
If generation fails, an existing report is left unchanged.

## Schedule the daily run

After a successful manual run, open PowerShell in this folder and run:

```powershell
.\install_daily_task.ps1
```

The setup script asks for the config path and daily run time in the computer's
local timezone. It creates a Windows Task Scheduler task under your user
account. The task only generates/overwrites the local HTML draft; it does not
send email. If a task with the same name already exists, setup stops rather
than replacing it. The computer must be on and the configured Windows account
must be signed in at the scheduled time.

## Calculation and data rules

- Issues in Jira's `Done` status category count as complete.
- The story-point field must be configured. Totals that include issues with
  missing estimates are marked unavailable; missing estimates are not treated
  as zero.

Blockers are highlighted when an issue has the configured blocked status and
its Jira `updated` time is at least `blocker_age_days` old. This uses last
update as the age signal; it does not establish when the issue first became
blocked.

Accomplishments and progress are drawn from issues in the active sprint at the
time the report runs. The daily task refreshes the current snapshot; it does
not retain historical snapshots or compare progress between runs.

## Jira data helper tools

Build a JQL query without connecting to Jira:

```powershell
python tools\build_jql.py --project SAM1 --status "In Progress" --updated-from 2026-11-01 --updated-through 2026-11-30
```

Validate a local Jira issue JSON export before using its metrics:

```powershell
python tools\validate_jira_issue_export.py issues.json --project SAM1 --story-points-field customfield_10016
```

The validator does not contact Jira. Use the confirmed story-point field ID;
missing or invalid values make the total unavailable rather than counting as
zero. Do not include credentials in exported data.

Discover story-point field candidates and check the active sprint:

```powershell
python tools\discover_story_points_field.py --base-url https://your-site.atlassian.net --board-id 1 --project-key SAM1 --email your-account@example.com --token-env JIRA_API_TOKEN
```

Verify the live active sprint and issue data against an expected sprint:

```powershell
python tools\verify_sprint_data.py --config config.json --expected-sprint-id 123
```

Both tools read the API token from an environment variable. Field discovery
and verification are read-only; the verifier prints issue details for local
review and does not generate or overwrite the HTML report.

## Tests

Run the offline unit tests without Jira credentials:

```powershell
python -m unittest discover -s tests -v
```
