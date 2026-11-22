#!/usr/bin/env python3
"""Check a local Jira issue export for reporting data quality."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def validate_issues(
    payload: Any,
    project_key: str,
    story_points_field: str,
) -> dict[str, Any]:
    if isinstance(payload, dict):
        issues = payload.get("issues")
    else:
        issues = payload
    if not isinstance(issues, list):
        raise ValueError("input must be a Jira issues array or an object with an issues array")

    errors: list[str] = []
    warnings: list[str] = []
    point_values: list[float] = []
    structurally_valid = 0

    for index, issue in enumerate(issues):
        label = f"issue[{index}]"
        issue_valid = True
        if not isinstance(issue, dict):
            errors.append(f"{label}: expected an issue object")
            continue

        key = issue.get("key")
        if isinstance(key, str) and key.strip():
            label = key.strip()
        else:
            errors.append(f"{label}: missing issue key")
            issue_valid = False

        fields = issue.get("fields")
        if not isinstance(fields, dict):
            errors.append(f"{label}: missing fields object")
            continue

        project = fields.get("project")
        actual_project = project.get("key") if isinstance(project, dict) else None
        if not isinstance(actual_project, str) or not actual_project.strip():
            errors.append(f"{label}: missing project key")
            issue_valid = False
        elif actual_project.casefold() != project_key.casefold():
            errors.append(
                f"{label}: project {actual_project!r} does not match {project_key!r}"
            )
            issue_valid = False

        status = fields.get("status")
        if (
            not isinstance(status, dict)
            or not isinstance(status.get("name"), str)
            or not status["name"].strip()
        ):
            errors.append(f"{label}: missing status name")
            issue_valid = False
        category = status.get("statusCategory") if isinstance(status, dict) else None
        if (
            not isinstance(category, dict)
            or not isinstance(category.get("name"), str)
            or not category["name"].strip()
        ):
            errors.append(f"{label}: missing status category")
            issue_valid = False

        if not _valid_timestamp(fields.get("updated")):
            warnings.append(f"{label}: updated timestamp is missing, invalid, or lacks a timezone")

        points = fields.get(story_points_field)
        if points is None:
            warnings.append(f"{label}: story points are unavailable")
        elif (
            isinstance(points, bool)
            or not isinstance(points, (int, float))
            or not math.isfinite(points)
            or points < 0
        ):
            warnings.append(f"{label}: story points are invalid")
        else:
            point_values.append(points)

        if issue_valid:
            structurally_valid += 1

    points_complete = len(point_values) == len(issues) and not errors
    return {
        "issue_count": len(issues),
        "structurally_valid_issue_count": structurally_valid,
        "story_points_total": sum(point_values) if points_complete else None,
        "story_points_status": "available" if points_complete else "unavailable",
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a local Jira issue export without contacting Jira."
    )
    parser.add_argument("input", type=Path, help="path to a Jira JSON issues export")
    parser.add_argument("--project", required=True, help="expected Jira project key")
    parser.add_argument(
        "--story-points-field",
        required=True,
        help="configured custom field ID, such as customfield_10016",
    )
    args = parser.parse_args()

    if not args.project.strip():
        parser.error("--project must not be empty")
    if not re.fullmatch(r"customfield_[0-9]+", args.story_points_field):
        parser.error("--story-points-field must look like customfield_10016")

    try:
        with args.input.open(encoding="utf-8") as input_file:
            payload = json.load(input_file)
        result = validate_issues(payload, args.project.strip(), args.story_points_field)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
