# Instruction File SRP Review Instructions

## When to use

Use this instruction when asked to review one or more agent instruction files
for adherence to the Single Responsibility Principle (SRP).

## Scope and review

- Review the files requested by the user. If no subset is specified, review all
  `*.agent.md` files in `instructions/`, including `main.agent.md` and this
  file.
- Read each target file and identify its primary responsibility from its
  trigger, purpose, and expected outcome.
- Pass a file when its procedures, safeguards, and output requirements all
  support that primary responsibility. Multiple steps do not by themselves
  indicate multiple responsibilities.
- Mark a file for review when it directs unrelated tasks, has independent
  outcomes, or combines responsibilities that could reasonably be maintained
  separately.
- Treat routing to focused instructions as the primary responsibility of
  `main.agent.md`.
- Consider overlap between files; distinguish useful handoffs from duplicated
  or conflicting ownership.
- Do not modify the reviewed files unless the user asks for changes.

## Output

Return a Markdown table with one row per reviewed file and these columns:

| File | Primary responsibility | SRP result | Evidence or concern |
| --- | --- | --- | --- |

Use `Pass` or `Review` for the SRP result. Follow the table with a brief
overall summary. Link workspace files in the response. If files are missing or
unreadable, identify them and do not infer their contents.
