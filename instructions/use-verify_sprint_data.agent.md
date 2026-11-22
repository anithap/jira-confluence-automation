# Instructions for `verify_sprint_data.py`

## When to use

Use `tools/verify_sprint_data.py` after configuring Jira and before accepting
the report workflow. It retrieves the configured board, exactly one active
sprint, and all paginated sprint issues through the report generator's Jira
client. It verifies the expected sprint and prints issue keys, statuses,
assignees, story points, timestamps, links, and aggregate counts.

## Invocation

Run from the workspace root with the configured token environment variable set:

```powershell
python tools\verify_sprint_data.py --config config.json --expected-sprint-id 123
```

Use `--expected-sprint-name` instead or in addition when the sprint ID is not
known. The script prints JSON for local review. It does not write the HTML
report or make Jira changes. Resolve any retrieval, project, sprint, status,
or estimate discrepancy before accepting the report.

Do not share the output without reviewing it; it may contain assignee names
and Jira issue links. Never put the API token in the configuration file or
command line.

## Execution and evidence

- When asked to verify sprint data, invoke the script and inspect its exit
  code and JSON output. Do not treat this instruction, a prior run, or a
  mocked test as evidence of a current live verification.
- Confirm that the supplied config file exists and that its configured token
  environment variable is available to the process without displaying the
  secret. If either prerequisite is missing, stop and report the task as
  blocked; do not claim Jira retrieval succeeded.
- Require the expected sprint ID or name from the user or another verified
  source. Do not guess it.
- Claim success only when the command exits successfully, reports
  `retrieval_complete: true`, and matches the expected sprint. Summarize only
  values present in its JSON output.
- If only offline tests can run, label them as offline tests and state that
  the live sprint has not been verified. Do not imply that mocked API data
  came from Jira.
