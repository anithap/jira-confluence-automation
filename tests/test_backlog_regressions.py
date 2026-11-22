import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError, URLError

import tools.discover_story_points_field as field_discovery
from generate_sprint_report import (
    JiraClient,
    ReportError,
    load_config,
    main as generate_main,
    summarize_issues,
    write_report_atomic,
)
from tools.discover_story_points_field import analyze_candidates
from tools.verify_sprint_data import verify_sprint


CONFIG = {
    "jira_base_url": "https://example.atlassian.net",
    "board_id": 12,
    "project_key": "SAM1",
    "jira_email": "user@example.test",
    "api_token_env": "TEST_JIRA_TOKEN",
    "story_points_field": "customfield_10016",
    "output_path": "",
}


def make_issue(key="SAM1-1", project="SAM1", points=3):
    return {
        "key": key,
        "fields": {
            "project": {"key": project},
            "summary": "Example",
            "status": {"name": "Done", "statusCategory": {"name": "Done"}},
            "assignee": {"displayName": "Example User"},
            "updated": "2026-11-20T12:00:00+00:00",
            "customfield_10016": points,
        },
    }


class BacklogRegressionTests(unittest.TestCase):
    def test_missing_configuration_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"project_key": "SAM1"}), encoding="utf-8")
            with self.assertRaisesRegex(ReportError, "Missing configuration values"):
                load_config(path)

    def test_missing_token_does_not_change_existing_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            output.write_text("previous report", encoding="utf-8")
            config = dict(CONFIG, output_path=str(output))
            config_path = Path(directory) / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            stderr = io.StringIO()
            with mock.patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(stderr):
                result = generate_main(["--config", str(config_path)])
            self.assertEqual(result, 1)
            self.assertEqual(output.read_text(encoding="utf-8"), "previous report")
            self.assertIn("environment variable TEST_JIRA_TOKEN is not set", stderr.getvalue())

    def test_incomplete_jira_retrieval_does_not_change_existing_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            output.write_text("previous report", encoding="utf-8")
            config = dict(CONFIG, output_path=str(output))
            config_path = Path(directory) / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            stderr = io.StringIO()
            with (
                mock.patch.dict(os.environ, {"TEST_JIRA_TOKEN": "test-token"}),
                mock.patch(
                    "generate_sprint_report.fetch_sprint_data",
                    side_effect=ReportError("incomplete Jira data"),
                ),
                contextlib.redirect_stderr(stderr),
            ):
                result = generate_main(["--config", str(config_path)])
            self.assertEqual(result, 1)
            self.assertEqual(output.read_text(encoding="utf-8"), "previous report")
            self.assertIn("incomplete Jira data", stderr.getvalue())

    def test_write_failure_preserves_existing_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            output.write_text("previous report", encoding="utf-8")
            with mock.patch("generate_sprint_report.os.replace", side_effect=OSError("disk error")):
                with self.assertRaisesRegex(ReportError, "Unable to write report"):
                    write_report_atomic(output, "new report")
            self.assertEqual(output.read_text(encoding="utf-8"), "previous report")

    def test_malformed_pagination_response_is_rejected(self):
        client = JiraClient("https://example.atlassian.net", "user@example.test", "token")
        with mock.patch.object(client, "get_json", return_value={"values": "not-a-list"}):
            with self.assertRaisesRegex(ReportError, "invalid paginated response"):
                client.get_all_values("/paged")

    def test_auth_failure_is_not_retried(self):
        client = JiraClient("https://example.atlassian.net", "user@example.test", "token")
        error = HTTPError("https://example.atlassian.net/path", 401, "Unauthorized", {}, None)
        with mock.patch("generate_sprint_report.urlopen", side_effect=error) as urlopen_mock:
            with self.assertRaisesRegex(ReportError, "authentication/permission failure"):
                client.get_json("/path")
        error.close()
        self.assertEqual(urlopen_mock.call_count, 1)

    def test_transient_request_failure_uses_bounded_retries(self):
        client = JiraClient("https://example.atlassian.net", "user@example.test", "token")
        with (
            mock.patch("generate_sprint_report.urlopen", side_effect=URLError("offline")) as urlopen_mock,
            mock.patch("generate_sprint_report.time.sleep"),
        ):
            with self.assertRaisesRegex(ReportError, "Unable to reach Jira"):
                client.get_json("/path")
        self.assertEqual(urlopen_mock.call_count, 3)

    def test_invalid_and_negative_story_points_are_unavailable(self):
        result = summarize_issues(
            [make_issue(points=-1), make_issue("SAM1-2", points=True)],
            {
                "jira_base_url": "https://example.atlassian.net",
                "story_points_field": "customfield_10016",
            },
        )
        self.assertIsNone(result["current_points"])
        self.assertEqual(result["missing_points"], 2)

    def test_field_discovery_counts_only_matching_project_values(self):
        candidates = [{"id": "customfield_10016", "name": "Story Points"}]
        issues = [
            make_issue(points=3),
            make_issue("SAM1-2", points=None),
            make_issue("OTHER-1", project="OTHER", points=100),
        ]
        result = analyze_candidates(candidates, issues, "SAM1")
        self.assertEqual(result[0]["project_sprint_issue_count"], 2)
        self.assertEqual(result[0]["field_returned_issue_count"], 2)
        self.assertEqual(result[0]["populated_valid_value_count"], 1)
        self.assertTrue(result[0]["available_on_project_sprint_issues"])

    def test_field_discovery_uses_metadata_and_active_sprint_issues(self):
        def fake_request(_base_url, _authorization, path, params=None):
            if path == "/rest/api/3/field":
                return [
                    {"id": "customfield_10016", "name": "Story Points"},
                    {"id": "customfield_10017", "name": "Effort"},
                ]
            if path.endswith("/sprint"):
                return {"values": [{"id": 8, "name": "Sprint 8"}], "isLast": True}
            if path.endswith("/issue"):
                return {
                    "values": [make_issue(points=3)],
                    "isLast": True,
                }
            raise AssertionError(f"Unexpected Jira endpoint: {path}")

        with mock.patch.object(field_discovery, "_request_json", side_effect=fake_request):
            result = field_discovery.discover(
                "https://example.atlassian.net",
                12,
                "SAM1",
                "user@example.test",
                "test-token",
            )
        self.assertEqual(result["sprint_id"], 8)
        self.assertEqual([field["id"] for field in result["candidates"]], ["customfield_10016"])
        self.assertEqual(result["candidates"][0]["populated_valid_value_count"], 1)

    def test_sprint_verification_rejects_an_unexpected_sprint(self):
        with self.assertRaisesRegex(ReportError, "does not match expected ID"):
            verify_sprint(
                {"name": "Board"},
                {"id": 8, "name": "Sprint 8"},
                [],
                {"project_key": "SAM1", "story_points_field": "customfield_10016"},
                expected_sprint_id=9,
            )

    def test_sprint_verification_returns_issue_and_metric_data(self):
        result = verify_sprint(
            {"name": "Board"},
            {"id": 8, "name": "Sprint 8"},
            [make_issue()],
            {
                "project_key": "SAM1",
                "board_id": 12,
                "jira_base_url": "https://example.atlassian.net",
                "story_points_field": "customfield_10016",
                "blocker_status": "Blocked",
                "blocker_age_days": 5,
            },
            expected_sprint_name="sprint 8",
        )
        self.assertTrue(result["retrieval_complete"])
        self.assertEqual(result["issue_count"], 1)
        self.assertEqual(result["story_points"]["total"], 3)
        self.assertEqual(result["issues"][0]["status"], "Done")


if __name__ == "__main__":
    unittest.main()
