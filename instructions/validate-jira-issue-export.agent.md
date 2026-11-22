# Jira Issue Export Validation Instructions

## When to use

Use `tools/validate_jira_issue_export.py` to check a local Jira JSON issue
export before calculating or reporting sprint metrics. This is useful for
confirming project consistency, required status fields, timestamps, and story
point data. It reads local data only and makes no Jira requests.

## Invocation

Run from the workspace root:

```powershell
python tools\validate_jira_issue_export.py issues.json --project SAM1 --story-points-field customfield_10016
```

The input must be either a JSON array of Jira issue objects or an object with
an `issues` array. Use the confirmed custom field ID; never guess it. The
script prints a JSON summary and exits nonzero for structural or project
errors.

## Data handling

- Treat missing, invalid, non-finite, boolean, or negative story-point values
  as unavailable; never replace them with zero.
- The story-point total is unavailable unless every issue has a valid value.
- Treat missing or timezone-free `updated` values as warnings; do not use them
  to claim a blocker meets an age threshold.
- Resolve project mismatches and structural errors before using the export.
- Do not include API tokens or other credentials in the export or command.

## Presenting results

Summarize issue count, structural errors, warnings, and whether the story-point
total is available. If unavailable, explain that the total cannot be calculated
reliably from the supplied data. Do not present an invalid or partial total as
complete.
