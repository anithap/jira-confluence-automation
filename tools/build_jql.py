#!/usr/bin/env python3
"""Build a Jira JQL query from validated command-line filters."""

from __future__ import annotations

import argparse
from datetime import date, timedelta


def _literal(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _parse_date(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD format") from exc
    if parsed.isoformat() != value:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD format")
    return parsed


def build_jql(
    project: str,
    statuses: list[str] | None = None,
    assignee: str | None = None,
    updated_from: date | None = None,
    updated_through: date | None = None,
) -> str:
    if not project.strip():
        raise ValueError("project must not be empty")
    if (updated_from is None) != (updated_through is None):
        raise ValueError("both updated_from and updated_through are required")
    if updated_from and updated_through and updated_from > updated_through:
        raise ValueError("updated_from must not be later than updated_through")

    clauses = [f"project = {_literal(project.strip())}"]
    clean_statuses = [status.strip() for status in statuses or []]
    if any(not status for status in clean_statuses):
        raise ValueError("status values must not be empty")
    if len(clean_statuses) == 1:
        clauses.append(f"status = {_literal(clean_statuses[0])}")
    elif clean_statuses:
        values = ", ".join(_literal(status) for status in clean_statuses)
        clauses.append(f"status in ({values})")

    if assignee is not None:
        if not assignee.strip():
            raise ValueError("assignee must not be empty")
        clauses.append(f"assignee = {_literal(assignee.strip())}")

    if updated_from and updated_through:
        clauses.append(f"updated >= {_literal(updated_from.isoformat())}")
        try:
            exclusive_end = updated_through + timedelta(days=1)
        except OverflowError as exc:
            raise ValueError("updated_through is outside the supported date range") from exc
        clauses.append(f"updated < {_literal(exclusive_end.isoformat())}")

    return " AND ".join(clauses) + " ORDER BY updated DESC"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Jira JQL query.")
    parser.add_argument("--project", required=True, help="Jira project key")
    parser.add_argument(
        "--status",
        action="append",
        default=[],
        help="exact Jira status name; repeat to match multiple statuses",
    )
    parser.add_argument("--assignee", help="assignee account ID or Jira user value")
    parser.add_argument("--updated-from", type=_parse_date, help="inclusive date (YYYY-MM-DD)")
    parser.add_argument(
        "--updated-through",
        type=_parse_date,
        help="inclusive date (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    try:
        print(
            build_jql(
                args.project,
                args.status,
                args.assignee,
                args.updated_from,
                args.updated_through,
            )
        )
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
