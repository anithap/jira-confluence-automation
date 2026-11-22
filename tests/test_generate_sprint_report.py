import unittest
from datetime import datetime, timezone

from generate_sprint_report import JiraClient, fetch_sprint_data, render_report, summarize_issues


CONFIG = {
    "jira_base_url": "https://example.atlassian.net",
    "project_key": "DEV",
    "board_id": 12,
    "story_points_field": "customfield_10016",
    "blocker_status": "Blocked",
    "blocker_age_days": 5,
}


def make_issue(key, status, category, points, updated, summary="Example issue"):
    return {
        "key": key,
        "fields": {
            "project": {"key": "DEV"},
            "summary": summary,
            "status": {"name": status, "statusCategory": {"name": category}},
            "assignee": {"displayName": "Alex Example"},
            "labels": [],
            "updated": updated,
            "customfield_10016": points,
        },
    }


class SprintReportTests(unittest.TestCase):
    def test_missing_story_points_make_totals_unavailable(self):
        issues = [
            make_issue("DEV-1", "Done", "Done", 3, "2026-11-20T00:00:00Z"),
            make_issue("DEV-2", "To Do", "To Do", None, "2026-11-22T00:00:00Z"),
        ]
        result = summarize_issues(
            issues,
            CONFIG,
            datetime(2026, 11, 23, tzinfo=timezone.utc),
        )
        self.assertIsNone(result["current_points"])
        self.assertEqual(result["completed_points"], 3)
        self.assertEqual(result["missing_points"], 1)
        self.assertIsNone(result["remaining_points"])
        self.assertIsNone(result["story_point_completion_percentage"])
        self.assertEqual(result["completion_percentage"], 50)

    def test_blocker_at_five_day_threshold_is_highlighted_but_newer_is_not(self):
        issues = [
            make_issue("DEV-1", "Blocked", "In Progress", 2, "2026-11-18T00:00:00Z"),
            make_issue("DEV-2", "Blocked", "In Progress", 1, "2026-11-19T00:00:00Z"),
            make_issue("DEV-4", "Blocked", "In Progress", 1, None),
            make_issue("DEV-3", "In Progress", "In Progress", 1, "2026-11-18T00:00:00Z"),
        ]
        result = summarize_issues(
            issues,
            CONFIG,
            datetime(2026, 11, 23, tzinfo=timezone.utc),
        )
        self.assertEqual([issue["key"] for issue in result["blockers"]], ["DEV-1"])
        self.assertEqual(result["blockers_without_update"], 1)

    def test_status_breakdown_and_story_point_completion_are_calculated(self):
        issues = [
            make_issue("DEV-1", "Done", "Done", 3, "2026-11-20T00:00:00Z"),
            make_issue("DEV-2", "Review", "In Progress", 2, "2026-11-22T00:00:00Z"),
            make_issue("DEV-3", "To Do", "To Do", 5, "2026-11-22T00:00:00Z"),
        ]
        result = summarize_issues(
            issues,
            CONFIG,
            datetime(2026, 11, 23, tzinfo=timezone.utc),
        )
        self.assertEqual(
            result["status_counts"],
            [
                {"status": "Done", "category": "Done", "count": 1},
                {"status": "Review", "category": "In Progress", "count": 1},
                {"status": "To Do", "category": "To Do", "count": 1},
            ],
        )
        self.assertEqual(result["remaining_issue_count"], 2)
        self.assertAlmostEqual(result["completion_percentage"], 100 / 3)
        self.assertEqual(result["remaining_points"], 7)
        self.assertEqual(result["story_point_completion_percentage"], 30)

    def test_empty_sprint_has_unavailable_completion_percentages(self):
        result = summarize_issues(
            [],
            CONFIG,
            datetime(2026, 11, 23, tzinfo=timezone.utc),
        )
        self.assertEqual(result["status_counts"], [])
        self.assertIsNone(result["completion_percentage"])
        self.assertIsNone(result["story_point_completion_percentage"])

    def test_issue_pagination_and_project_key_matching(self):
        first_issue = make_issue("DEV-1", "To Do", "To Do", 1, "2026-11-22T00:00:00Z")
        second_issue = make_issue("DEV-2", "Done", "Done", 2, "2026-11-22T00:00:00Z")

        class FakeClient:
            def get_json(self, path, params=None):
                if path.endswith("/board/12"):
                    return {"name": "Engineering"}
                if path.endswith("/sprint"):
                    return {"values": [{"id": 8, "name": "Sprint 8"}], "isLast": True}
                raise AssertionError(f"Unexpected endpoint: {path}")

            def get_all_values(self, path, params=None):
                if path.endswith("/sprint"):
                    return [{"id": 8, "name": "Sprint 8"}]
                return [first_issue, second_issue]

        client = FakeClient()
        board, sprint, issues = fetch_sprint_data(client, CONFIG)
        self.assertEqual(board["name"], "Engineering")
        self.assertEqual(sprint["id"], 8)
        self.assertEqual([issue["key"] for issue in issues], ["DEV-1", "DEV-2"])

    def test_pagination_continues_when_jira_marks_a_short_page_nonfinal(self):
        client = JiraClient("https://example.atlassian.net", "user@example.test", "token")
        pages = [
            {"values": [{"id": 1}], "isLast": False},
            {"values": [{"id": 2}], "isLast": True},
        ]
        starts = []

        def fake_get_json(path, params=None):
            starts.append(params["startAt"])
            return pages.pop(0)

        client.get_json = fake_get_json
        self.assertEqual(client.get_all_values("/paged"), [{"id": 1}, {"id": 2}])
        self.assertEqual(starts, [0, 1])

    def test_render_escapes_jira_text_and_shows_progress_sections(self):
        issue = make_issue(
            "DEV-4",
            "In Progress",
            "In Progress",
            1,
            "2026-11-22T00:00:00Z",
            "<script>alert(1)</script>",
        )
        report = render_report(
            {"name": "Engineering"},
            {"name": "Sprint 8", "startDate": "2026-11-10", "endDate": "2026-11-24"},
            [issue],
            CONFIG,
            datetime(2026, 11, 23, tzinfo=timezone.utc),
        )
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", report)
        self.assertNotIn("<script>alert(1)</script>", report)
        self.assertIn("Story-point completion", report)
        self.assertIn("0.0%", report)
        self.assertIn("https://example.atlassian.net/browse/DEV-4", report)
        self.assertIn("<h2>Accomplishments</h2>", report)
        self.assertIn("<h2>Status breakdown</h2>", report)
        self.assertIn("<h2>Work completion</h2>", report)
        self.assertIn("Issue completion", report)
        self.assertIn("<h2>Blockers and risks</h2>", report)


if __name__ == "__main__":
    unittest.main()
