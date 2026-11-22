# Building Jira JQL Instructions

## When to use

Use `tools/build_jql.py` when the user needs a JQL string filtered by Jira
project, status, assignee, or an `updated` date range. The script constructs a
query only; it does not connect to Jira or run the query.

## Invocation

Run from the workspace root:

```powershell
python tools\build_jql.py --project SAM1 --status "In Progress" --assignee "account-id" --updated-from 2026-11-01 --updated-through 2026-11-30
```

- `--project` is required.
- Repeat `--status` to include multiple exact Jira status names.
- `--assignee` accepts a Jira account ID or Jira-compatible user value.
- Supply both date options or neither. Both dates use `YYYY-MM-DD`; the range
  includes the full `updated-through` date.

Use the printed query exactly as generated. Do not concatenate unescaped user
values into JQL yourself. If inputs are invalid or the date range is reversed,
explain the error and ask for corrected values; do not invent filters.

## Presenting results

Show the generated JQL in a code block and state that it has not been executed.
Only report Jira results after an authorized Jira query has actually run.
