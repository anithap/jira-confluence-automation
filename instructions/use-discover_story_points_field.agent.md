# Instructions for `discover_story_points_field.py`

## When to use

Use `tools/discover_story_points_field.py` to inspect Jira field metadata and
check candidate story-point fields against the configured board's one active
sprint. Do not guess or hard-code a field ID.

## Invocation

Run from the workspace root after setting the API token in the environment:

```powershell
python tools\discover_story_points_field.py --base-url https://example.atlassian.net --board-id 1 --project-key SAM1 --email account@example.com --token-env JIRA_API_TOKEN
```

The script requires HTTPS and reads the secret from the named environment
variable. It reports candidate custom field IDs, how many project sprint
issues returned each field, and how many values were populated and valid. It
does not modify Jira or expose the token.

If there are no candidates, multiple plausible candidates, no active sprint,
or no project sprint issues, report that field confirmation is unresolved.
Have the Jira administrator or project owner confirm the intended field before
using it in report configuration.

## Execution and evidence

- When asked to perform discovery, run the script; do not answer from this
  instruction, prior output, or a mocked test.
- Check that the token variable is available to the process that will run the
  script without printing or exposing its value. If it is unavailable, stop
  and report the task as blocked; do not claim that Jira was queried.
- Use the actual Jira base URL, board ID, project key, and account email.
  Never invent missing parameters or field IDs.
- Claim live discovery only when the script exits successfully and returns
  Jira field and sprint-issue data. Report candidate IDs and their returned
  and populated issue counts from that output.
- If execution fails or output is ambiguous, report the exact limitation.
  Clearly label mocked or unit-test evidence as offline; it does not establish
  live Jira field availability.
