#!/usr/bin/env python3
"""Generate a deterministic HTML report for one active Jira sprint."""

from __future__ import annotations

import argparse
import base64
import html
import json
import math
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen


class ReportError(Exception):
    """An expected configuration, Jira, or report-generation error."""


def load_config(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as config_file:
            config = json.load(config_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise ReportError(f"Unable to read configuration: {exc}") from exc

    if not isinstance(config, dict):
        raise ReportError("Configuration must be a JSON object.")

    required = (
        "jira_base_url",
        "board_id",
        "project_key",
        "jira_email",
        "api_token_env",
        "story_points_field",
        "output_path",
    )
    missing = [key for key in required if config.get(key) in (None, "")]
    if missing:
        raise ReportError(f"Missing configuration values: {', '.join(missing)}.")

    base_url = config["jira_base_url"]
    parsed_url = urlsplit(base_url if isinstance(base_url, str) else "")
    if (
        parsed_url.scheme != "https"
        or not parsed_url.netloc
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise ReportError("jira_base_url must be an HTTPS URL without a query or fragment.")
    if not isinstance(config["board_id"], int) or isinstance(config["board_id"], bool) or config["board_id"] < 1:
        raise ReportError("board_id must be a positive integer.")
    for key in ("project_key", "jira_email", "output_path"):
        if not isinstance(config[key], str) or not config[key].strip():
            raise ReportError(f"{key} must be a non-empty string.")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(config["api_token_env"])):
        raise ReportError("api_token_env must be a valid environment variable name.")
    if not re.fullmatch(r"customfield_[0-9]+", str(config["story_points_field"])):
        raise ReportError("story_points_field must be a Jira field ID such as customfield_10016.")

    blocker_status = config.get("blocker_status", "Blocked")
    if not isinstance(blocker_status, str) or not blocker_status.strip():
        raise ReportError("blocker_status must be a non-empty status name.")

    age_days = config.get("blocker_age_days", 5)
    if not isinstance(age_days, (int, float)) or isinstance(age_days, bool) or not math.isfinite(age_days) or age_days < 0:
        raise ReportError("blocker_age_days must be a non-negative number.")
    threshold = config.get("health_threshold_percent", 80)
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or not 0 <= threshold <= 100:
        raise ReportError("health_threshold_percent must be between 0 and 100.")
    return config


class JiraClient:
    def __init__(self, base_url: str, email: str, token: str, timeout: int = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.authorization = "Basic " + base64.b64encode(f"{email}:{token}".encode("utf-8")).decode("ascii")
        self.timeout = timeout

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        request = Request(
            url,
            headers={
                "Authorization": self.authorization,
                "Accept": "application/json",
                "User-Agent": "local-jira-sprint-status/1.0",
            },
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ReportError("Jira returned an unexpected response format.")
                return payload
            except HTTPError as exc:
                if exc.code == 429 or 500 <= exc.code < 600:
                    if attempt < 2:
                        retry_after = exc.headers.get("Retry-After", "")
                        delay = min(int(retry_after), 10) if retry_after.isdigit() else 1 + attempt
                        time.sleep(delay)
                        continue
                if exc.code in (401, 403):
                    raise ReportError(f"Jira authentication/permission failure (HTTP {exc.code}).") from exc
                raise ReportError(f"Jira request failed (HTTP {exc.code}) for {path}.") from exc
            except (URLError, TimeoutError) as exc:
                if attempt < 2:
                    time.sleep(1 + attempt)
                    continue
                reason = getattr(exc, "reason", exc)
                raise ReportError(f"Unable to reach Jira for {path}: {reason}") from exc
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ReportError(f"Jira returned invalid JSON for {path}.") from exc
        raise ReportError(f"Jira request failed after retries for {path}.")

    def get_all_values(self, path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        values: list[dict[str, Any]] = []
        start_at = 0
        page_size = 50
        for _ in range(100):
            page_params = dict(params or {})
            page_params.update({"startAt": start_at, "maxResults": page_size})
            page = self.get_json(path, page_params)
            page_values = page.get("values")
            if not isinstance(page_values, list) or not all(isinstance(item, dict) for item in page_values):
                raise ReportError(f"Jira returned an invalid paginated response for {path}.")
            values.extend(page_values)
            if page.get("isLast") is True:
                return values
            if page.get("isLast") is not False and len(page_values) < page_size:
                return values
            if not page_values:
                raise ReportError(f"Jira pagination made no progress for {path}.")
            start_at += len(page_values)
        raise ReportError(f"Jira returned too many pages for {path}; refusing a partial report.")


def fetch_sprint_data(client: JiraClient, config: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    board_id = config["board_id"]
    board = client.get_json(f"/rest/agile/1.0/board/{board_id}")
    sprints = client.get_all_values(f"/rest/agile/1.0/board/{board_id}/sprint", {"state": "active"})
    if len(sprints) != 1:
        raise ReportError(f"Expected exactly one active sprint on board {board_id}; found {len(sprints)}.")
    sprint = sprints[0]
    sprint_id = sprint.get("id")
    if not isinstance(sprint_id, int):
        raise ReportError("The active sprint response did not contain a valid sprint ID.")

    fields = [
        "project",
        "summary",
        "status",
        "assignee",
        "priority",
        "issuetype",
        "labels",
        "updated",
        config["story_points_field"],
    ]
    issues = client.get_all_values(
        f"/rest/agile/1.0/sprint/{sprint_id}/issue",
        {"fields": ",".join(fields)},
    )
    project_issues = []
    for issue in issues:
        fields = issue.get("fields")
        project = fields.get("project") if isinstance(fields, dict) else None
        if not isinstance(project, dict) or not isinstance(project.get("key"), str):
            raise ReportError(f"Jira issue {issue.get('key', 'Unavailable')} is missing its project key.")
        if project["key"].casefold() == config["project_key"].casefold():
            project_issues.append(issue)
    return board, sprint, project_issues


def _issue_details(issue: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    fields = issue.get("fields") or {}
    status = fields.get("status") or {}
    category = status.get("statusCategory") or {}
    assignee = fields.get("assignee") or {}
    priority = fields.get("priority") or {}
    issue_type = fields.get("issuetype") or {}
    story_points = fields.get(config["story_points_field"])
    if isinstance(story_points, bool) or not isinstance(story_points, (int, float)) or not math.isfinite(story_points) or story_points < 0:
        story_points = None
    return {
        "key": str(issue.get("key") or "Unavailable"),
        "summary": str(fields.get("summary") or "Unavailable"),
        "status": str(status.get("name") or "Unavailable"),
        "category": str(category.get("name") or ""),
        "assignee": str(assignee.get("displayName") or "Unassigned"),
        "priority": str(priority.get("name") or "Unavailable"),
        "issue_type": str(issue_type.get("name") or "Unavailable"),
        "labels": fields.get("labels") if isinstance(fields.get("labels"), list) else [],
        "updated": fields.get("updated"),
        "story_points": story_points,
        "url": f"{config['jira_base_url'].rstrip('/')}/browse/{quote(str(issue.get('key') or ''), safe='')}",
    }


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def summarize_issues(
    issues: list[dict[str, Any]],
    config: dict[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    details = [_issue_details(issue, config) for issue in issues]
    done = [issue for issue in details if issue["category"].casefold() == "done"]
    in_progress = [issue for issue in details if issue["category"].casefold() == "in progress"]
    not_started = [issue for issue in details if issue["category"].casefold() == "to do"]
    blocker_status = config.get("blocker_status", "Blocked").casefold()
    age_limit = timedelta(days=config.get("blocker_age_days", 5))
    blockers = []
    blockers_without_update = 0
    for issue in details:
        is_blocked = issue["status"].casefold() == blocker_status
        updated = _parse_timestamp(issue["updated"])
        issue["updated_display"] = updated.strftime("%Y-%m-%d %H:%M UTC") if updated else "Unavailable"
        if is_blocked:
            if updated is None:
                blockers_without_update += 1
            elif now - updated >= age_limit:
                blockers.append(issue)

    status_counts_by_pair: dict[tuple[str, str], int] = {}
    for issue in details:
        key = (issue["status"], issue["category"] or "Unavailable")
        status_counts_by_pair[key] = status_counts_by_pair.get(key, 0) + 1
    status_counts = [
        {"status": status, "category": category, "count": count}
        for (status, category), count in sorted(status_counts_by_pair.items())
    ]
    missing_points = sum(issue["story_points"] is None for issue in details)
    missing_done_points = sum(issue["story_points"] is None for issue in done)
    current_points = None if missing_points else sum(issue["story_points"] for issue in details)
    completed_points = None if missing_done_points else sum(issue["story_points"] for issue in done)
    remaining_points = (
        current_points - completed_points
        if current_points is not None and completed_points is not None
        else None
    )
    total_issue_count = len(details)
    completion_percentage = len(done) / total_issue_count * 100 if total_issue_count else None
    story_point_completion_percentage = (
        completed_points / current_points * 100
        if completed_points is not None and current_points is not None and current_points > 0
        else None
    )
    return {
        "issues": details,
        "done": done,
        "in_progress": in_progress,
        "not_started": not_started,
        "status_counts": status_counts,
        "total_issue_count": total_issue_count,
        "completed_issue_count": len(done),
        "remaining_issue_count": total_issue_count - len(done),
        "completion_percentage": completion_percentage,
        "blockers": blockers,
        "blockers_without_update": blockers_without_update,
        "current_points": current_points,
        "completed_points": completed_points,
        "remaining_points": remaining_points,
        "story_point_completion_percentage": story_point_completion_percentage,
        "missing_points": missing_points,
        "missing_done_points": missing_done_points,
    }


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _format_percentage(value: float | None) -> str:
    return f"{value:.1f}%" if value is not None else "Unavailable"


def _issue_list(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return "<p>None.</p>"
    items = []
    for issue in issues:
        items.append(
            "<li><a href=\"{url}\">{key}</a> — {summary} "
            "({status}; {assignee}; updated {updated})</li>".format(
                url=_escape(issue["url"]),
                key=_escape(issue["key"]),
                summary=_escape(issue["summary"]),
                status=_escape(issue["status"]),
                assignee=_escape(issue["assignee"]),
                updated=_escape(issue["updated_display"]),
            )
        )
    return "<ul>" + "".join(items) + "</ul>"


def render_report(
    board: dict[str, Any],
    sprint: dict[str, Any],
    issues: list[dict[str, Any]],
    config: dict[str, Any],
    generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or datetime.now(timezone.utc)
    summary = summarize_issues(issues, config, generated_at)
    sprint_name = sprint.get("name") or "Unavailable"
    start = sprint.get("startDate") or "Unavailable"
    end = sprint.get("endDate") or "Unavailable"
    board_name = board.get("name") or "Unavailable"
    points = (
        f"{summary['current_points']:g}"
        if summary["current_points"] is not None
        else f"Unavailable (story points missing for {summary['missing_points']} issue(s))"
    )
    completed_points = (
        f"{summary['completed_points']:g}"
        if summary["completed_points"] is not None
        else f"Unavailable (story points missing for {summary['missing_done_points']} completed issue(s))"
    )
    remaining_points = (
        f"{summary['remaining_points']:g}"
        if summary["remaining_points"] is not None
        else "Unavailable"
    )
    blockers_note_parts = []
    if summary["blockers"]:
        blockers_note_parts.append(f"{len(summary['blockers'])} blocker(s) highlighted.")
    elif not summary["blockers_without_update"]:
        blockers_note_parts.append(
            f"No blockers highlighted (configured rule: at least {config.get('blocker_age_days', 5):g} days since last update)."
        )
    if summary["blockers_without_update"]:
        blockers_note_parts.append(
            f"{summary['blockers_without_update']} matching blocker(s) could not be assessed because last-updated time is unavailable."
        )
    blockers_note = " ".join(blockers_note_parts)
    summary_text = (
        f"{summary['completed_issue_count']} of {summary['total_issue_count']} issues are complete "
        f"({_format_percentage(summary['completion_percentage'])}); "
        f"{len(summary['in_progress'])} issue(s) are in progress and "
        f"{len(summary['not_started'])} have not started. "
        f"Completed story points: {completed_points}; remaining story points: {remaining_points}."
    )
    risk_items = []
    if summary["blockers"]:
        risk_items.append(f"{len(summary['blockers'])} blocker(s) have not been updated within the configured age threshold.")
    if summary["blockers_without_update"]:
        risk_items.append(f"{summary['blockers_without_update']} matching blocker(s) have no usable last-updated timestamp.")
    if summary["missing_points"]:
        risk_items.append(f"Story points are missing for {summary['missing_points']} issue(s); the current total is unavailable.")
    risks_html = "<ul>" + "".join(f"<li>{_escape(item)}</li>" for item in risk_items) + "</ul>"
    timestamp = generated_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status_rows = "".join(
        "<tr><td>{status}</td><td>{category}</td><td>{count}</td></tr>".format(
            status=_escape(item["status"]),
            category=_escape(item["category"]),
            count=item["count"],
        )
        for item in summary["status_counts"]
    )
    if not status_rows:
        status_rows = '<tr><td colspan="3">No issues in the active sprint.</td></tr>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jira Sprint Status — {_escape(sprint_name)}</title>
<style>
:root {{ color-scheme: light; font-family: system-ui, sans-serif; color: #172b4d; background: #f4f5f7; }}
body {{ margin: 0 auto; max-width: 960px; padding: 1.5rem; }}
header, section {{ background: white; border: 1px solid #dfe1e6; border-radius: 8px; margin: 1rem 0; padding: 1rem 1.25rem; }}
h1, h2 {{ margin-top: 0; }}
dl {{ display: grid; grid-template-columns: minmax(9rem, 1fr) 2fr; gap: .5rem 1rem; }}
dt {{ font-weight: 650; }} dd {{ margin: 0; overflow-wrap: anywhere; }}
li {{ margin: .55rem 0; }} a {{ color: #0747a6; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid #dfe1e6; padding: .55rem; text-align: left; }}
.unavailable {{ color: #6b778c; }}
@media (max-width: 560px) {{ body {{ padding: .5rem; }} dl {{ grid-template-columns: 1fr; gap: .2rem; }} dd {{ margin-bottom: .6rem; }} }}
</style>
</head>
<body>
<header>
<h1>Jira Sprint Status</h1>
<p>Daily stakeholder draft · Data refreshed: {_escape(timestamp)} · Review before manual distribution.</p>
<dl>
<dt>Sprint</dt><dd>{_escape(sprint_name)}</dd>
<dt>Sprint dates</dt><dd>{_escape(start)} — {_escape(end)}</dd>
<dt>Project</dt><dd>{_escape(config["project_key"])}</dd>
<dt>Board</dt><dd>{_escape(board_name)} (ID {_escape(config["board_id"])})</dd>
<dt>Issue completion</dt><dd>{summary['completed_issue_count']} of {summary['total_issue_count']} issues · {_escape(_format_percentage(summary['completion_percentage']))}</dd>
<dt>Story points</dt><dd>{_escape(points)}</dd>
<dt>Completed story points</dt><dd>{_escape(completed_points)}</dd>
<dt>Remaining story points</dt><dd>{_escape(remaining_points)}</dd>
<dt>Story-point completion</dt><dd>{_escape(_format_percentage(summary['story_point_completion_percentage']))}</dd>
</dl>
</header>
<section><h2>Executive summary</h2><p>{_escape(summary_text)}</p></section>
<section><h2>Status breakdown</h2>
<table><thead><tr><th>Status</th><th>Category</th><th>Issues</th></tr></thead><tbody>{status_rows}</tbody></table>
</section>
<section><h2>Work completion</h2>
<ul>
<li>Completed: {summary['completed_issue_count']} of {summary['total_issue_count']} issues ({_escape(_format_percentage(summary['completion_percentage']))})</li>
<li>Remaining: {summary['remaining_issue_count']} issues</li>
<li>In progress: {len(summary['in_progress'])} issues</li>
<li>Not started: {len(summary['not_started'])} issues</li>
<li>Current sprint story points: {_escape(points)}</li>
<li>Completed story points: {_escape(completed_points)}</li>
<li>Remaining story points: {_escape(remaining_points)}</li>
<li>Story-point completion: {_escape(_format_percentage(summary['story_point_completion_percentage']))}</li>
</ul>
</section>
<section><h2>Accomplishments</h2>{_issue_list(summary["done"])}</section>
<section><h2>In-progress work ({len(summary['in_progress'])})</h2>{_issue_list(summary["in_progress"])}</section>
<section><h2>Blockers and risks</h2><p>{_escape(blockers_note)}</p>{_issue_list(summary["blockers"])}{risks_html}</section>
<section><h2>Not started ({len(summary['not_started'])})</h2>{_issue_list(summary["not_started"])}</section>
<footer><p>Data refreshed at {_escape(timestamp)}. Accomplishments and progress reflect the current active sprint at generation time. Blockers are detected using the configured status and Jira's last-updated timestamp.</p></footer>
</body>
</html>
"""


def write_report_atomic(path: Path, content: str) -> None:
    temporary_path: str | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    except OSError as exc:
        raise ReportError(f"Unable to write report to {path}: {exc}") from exc
    finally:
        if temporary_path and os.path.exists(temporary_path):
            try:
                os.unlink(temporary_path)
            except OSError:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a local HTML report for the active Jira sprint.")
    parser.add_argument("--config", required=True, help="Path to the JSON configuration file.")
    args = parser.parse_args(argv)
    try:
        config = load_config(Path(args.config))
        token = os.environ.get(config["api_token_env"])
        if not token:
            raise ReportError(f"Jira API token environment variable {config['api_token_env']} is not set.")
        client = JiraClient(config["jira_base_url"], config["jira_email"], token)
        board, sprint, issues = fetch_sprint_data(client, config)
        report = render_report(board, sprint, issues, config)
        write_report_atomic(Path(config["output_path"]), report)
    except ReportError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Report generated: {config['output_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
