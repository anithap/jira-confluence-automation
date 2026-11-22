#!/usr/bin/env python3
"""Retrieve and validate live sprint data without writing a report."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generate_sprint_report import (  # noqa: E402
    JiraClient,
    ReportError,
    fetch_sprint_data,
    load_config,
    summarize_issues,
)


def verify_sprint(
    board: dict,
    sprint: dict,
    issues: list[dict],
    config: dict,
    expected_sprint_id: int | None = None,
    expected_sprint_name: str | None = None,
) -> dict:
    if expected_sprint_id is not None and sprint.get("id") != expected_sprint_id:
        raise ReportError(
            f"Active sprint ID {sprint.get('id')!r} does not match expected "
            f"ID {expected_sprint_id}."
        )
    if (
        expected_sprint_name is not None
        and str(sprint.get("name", "")).casefold() != expected_sprint_name.casefold()
    ):
        raise ReportError(
            f"Active sprint name {sprint.get('name')!r} does not match expected "
            f"name {expected_sprint_name!r}."
        )

    metrics = summarize_issues(issues, config)
    issue_details = []
    for issue in issues:
        fields = issue.get("fields") or {}
        status = fields.get("status") or {}
        assignee = fields.get("assignee") or {}
        issue_details.append(
            {
                "key": issue.get("key"),
                "status": status.get("name"),
                "assignee": assignee.get("displayName"),
                "story_points": fields.get(config["story_points_field"]),
                "updated": fields.get("updated"),
                "url": (
                    f"{config['jira_base_url'].rstrip('/')}/browse/{issue.get('key', '')}"
                ),
            }
        )
    return {
        "retrieval_complete": True,
        "project_key": config["project_key"],
        "board": {"id": config["board_id"], "name": board.get("name")},
        "sprint": {
            "id": sprint.get("id"),
            "name": sprint.get("name"),
            "start_date": sprint.get("startDate"),
            "end_date": sprint.get("endDate"),
        },
        "issue_count": len(issues),
        "status_counts": metrics["status_counts"],
        "story_points": {
            "total": metrics["current_points"],
            "completed": metrics["completed_points"],
            "remaining": metrics["remaining_points"],
            "missing_issue_count": metrics["missing_points"],
        },
        "issues": issue_details,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the configured board's active sprint and issue data."
    )
    parser.add_argument("--config", required=True, help="Path to the JSON configuration file")
    parser.add_argument("--expected-sprint-id", type=int, help="expected active sprint ID")
    parser.add_argument("--expected-sprint-name", help="expected active sprint name")
    args = parser.parse_args(argv)
    if args.expected_sprint_id is None and not args.expected_sprint_name:
        parser.error("provide --expected-sprint-id and/or --expected-sprint-name")

    try:
        config = load_config(Path(args.config))
        token = os.environ.get(config["api_token_env"])
        if not token:
            raise ReportError(
                f"Jira API token environment variable {config['api_token_env']} is not set."
            )
        client = JiraClient(
            config["jira_base_url"],
            config["jira_email"],
            token,
        )
        board, sprint, issues = fetch_sprint_data(client, config)
        result = verify_sprint(
            board,
            sprint,
            issues,
            config,
            args.expected_sprint_id,
            args.expected_sprint_name,
        )
    except ReportError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
