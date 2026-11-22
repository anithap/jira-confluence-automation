#!/usr/bin/env python3
"""Discover Jira story-point field candidates and check sprint availability."""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import re
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


class DiscoveryError(Exception):
    """An expected input, Jira API, or response error."""


def _request_json(
    base_url: str,
    authorization: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> Any:
    url = f"{base_url.rstrip('/')}{path}"
    if params:
        url = f"{url}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "Authorization": authorization,
            "Accept": "application/json",
            "User-Agent": "local-jira-field-discovery/1.0",
        },
    )
    for attempt in range(3):
        try:
            with urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if (exc.code == 429 or 500 <= exc.code < 600) and attempt < 2:
                retry_after = exc.headers.get("Retry-After", "")
                delay = min(int(retry_after), 10) if retry_after.isdigit() else 1 + attempt
                time.sleep(delay)
                continue
            if exc.code in (401, 403):
                raise DiscoveryError(
                    f"Jira authentication/permission failure (HTTP {exc.code})."
                ) from exc
            raise DiscoveryError(f"Jira request failed (HTTP {exc.code}) for {path}.") from exc
        except (URLError, TimeoutError) as exc:
            if attempt < 2:
                time.sleep(1 + attempt)
                continue
            raise DiscoveryError(f"Unable to reach Jira for {path}.") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DiscoveryError(f"Jira returned invalid JSON for {path}.") from exc
    raise DiscoveryError(f"Jira request failed after retries for {path}.")


def _get_all_values(
    base_url: str,
    authorization: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    start_at = 0
    page_size = 50
    for _ in range(100):
        page_params = dict(params or {})
        page_params.update({"startAt": start_at, "maxResults": page_size})
        page = _request_json(base_url, authorization, path, page_params)
        if not isinstance(page, dict):
            raise DiscoveryError(f"Jira returned an invalid paginated response for {path}.")
        page_values = page.get("values")
        if not isinstance(page_values, list) or not all(
            isinstance(item, dict) for item in page_values
        ):
            raise DiscoveryError(f"Jira returned an invalid paginated response for {path}.")
        values.extend(page_values)
        if page.get("isLast") is True:
            return values
        if page.get("isLast") is not False and len(page_values) < page_size:
            return values
        if not page_values:
            raise DiscoveryError(f"Jira pagination made no progress for {path}.")
        start_at += len(page_values)
    raise DiscoveryError(f"Jira returned too many pages for {path}; refusing partial results.")


def analyze_candidates(
    candidates: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    project_key: str,
) -> list[dict[str, Any]]:
    project_issues: list[tuple[str, dict[str, Any]]] = []
    for issue in issues:
        fields = issue.get("fields")
        project = fields.get("project") if isinstance(fields, dict) else None
        actual_key = project.get("key") if isinstance(project, dict) else None
        issue_key = issue.get("key")
        if not isinstance(actual_key, str) or not isinstance(issue_key, str):
            raise DiscoveryError("A sprint issue is missing its key or project key.")
        if actual_key.casefold() == project_key.casefold():
            project_issues.append((issue_key, fields))

    results = []
    for candidate in candidates:
        field_id = candidate["id"]
        returned_count = 0
        populated_count = 0
        invalid_count = 0
        for _, fields in project_issues:
            if field_id in fields:
                returned_count += 1
                value = fields[field_id]
                if value is not None:
                    if (
                        isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or not math.isfinite(value)
                        or value < 0
                    ):
                        invalid_count += 1
                    else:
                        populated_count += 1

        results.append(
            {
                "id": field_id,
                "name": candidate["name"],
                "project_sprint_issue_count": len(project_issues),
                "field_returned_issue_count": returned_count,
                "populated_valid_value_count": populated_count,
                "invalid_value_count": invalid_count,
                "available_on_project_sprint_issues": (
                    bool(project_issues) and returned_count == len(project_issues)
                ),
            }
        )
    return results


def discover(
    base_url: str,
    board_id: int,
    project_key: str,
    email: str,
    token: str,
) -> dict[str, Any]:
    parsed = urlsplit(base_url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise DiscoveryError("base_url must be an HTTPS URL without credentials or a query.")
    if board_id < 1:
        raise DiscoveryError("board_id must be a positive integer.")
    if not project_key.strip() or not email.strip() or not token:
        raise DiscoveryError("project_key, email, and token must not be empty.")

    authorization = "Basic " + base64.b64encode(
        f"{email}:{token}".encode("utf-8")
    ).decode("ascii")
    fields = _request_json(base_url, authorization, "/rest/api/3/field")
    if not isinstance(fields, list) or not all(isinstance(item, dict) for item in fields):
        raise DiscoveryError("Jira returned an invalid fields response.")

    candidates = [
        {"id": field.get("id"), "name": field.get("name")}
        for field in fields
        if isinstance(field.get("id"), str)
        and field["id"].startswith("customfield_")
        and isinstance(field.get("name"), str)
        and "story point" in field["name"].casefold()
    ]
    candidates.sort(key=lambda item: (item["name"].casefold(), item["id"]))
    if not candidates:
        raise DiscoveryError("No custom fields with 'story point' in the name were found.")

    sprints = _get_all_values(
        base_url,
        authorization,
        f"/rest/agile/1.0/board/{board_id}/sprint",
        {"state": "active"},
    )
    if len(sprints) != 1:
        raise DiscoveryError(
            f"Expected exactly one active sprint on board {board_id}; found {len(sprints)}."
        )
    sprint_id = sprints[0].get("id")
    if not isinstance(sprint_id, int) or isinstance(sprint_id, bool):
        raise DiscoveryError("The active sprint response did not contain a valid sprint ID.")

    fields_param = ",".join(["project", *(candidate["id"] for candidate in candidates)])
    issues = _get_all_values(
        base_url,
        authorization,
        f"/rest/agile/1.0/sprint/{sprint_id}/issue",
        {"fields": fields_param},
    )
    return {
        "board_id": board_id,
        "sprint_id": sprint_id,
        "sprint_name": sprints[0].get("name"),
        "project_key": project_key,
        "candidates": analyze_candidates(candidates, issues, project_key),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find Jira story-point fields and check them against the active sprint."
    )
    parser.add_argument("--base-url", required=True, help="Jira HTTPS base URL")
    parser.add_argument("--board-id", required=True, type=int, help="Jira Scrum board ID")
    parser.add_argument("--project-key", required=True, help="expected Jira project key")
    parser.add_argument("--email", required=True, help="Atlassian account email")
    parser.add_argument(
        "--token-env",
        default="JIRA_API_TOKEN",
        help="environment variable containing the API token (default: JIRA_API_TOKEN)",
    )
    args = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", args.token_env):
        parser.error("--token-env must be a valid environment variable name")
    token = os.environ.get(args.token_env)
    if not token:
        parser.error(f"token environment variable {args.token_env} is not set")

    try:
        result = discover(args.base_url, args.board_id, args.project_key, args.email, token)
    except DiscoveryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
