import unittest
from datetime import date

from tools.build_jql import build_jql
from tools.validate_jira_issue_export import validate_issues


class BuildJqlTests(unittest.TestCase):
    def test_builds_escaped_filters_and_inclusive_date_range(self):
        query = build_jql(
            'SAM"1',
            ['In Progress', 'Won\\t'],
            'account"id',
            date(2026, 11, 1),
            date(2026, 11, 30),
        )
        self.assertEqual(
            query,
            'project = "SAM\\"1" AND status in ("In Progress", "Won\\\\t") '
            'AND assignee = "account\\"id" AND updated >= "2026-11-01" '
            'AND updated < "2026-12-01" ORDER BY updated DESC',
        )

    def test_rejects_incomplete_or_reversed_date_range(self):
        with self.assertRaisesRegex(ValueError, "both updated_from"):
            build_jql("SAM1", updated_from=date(2026, 11, 1))
        with self.assertRaisesRegex(ValueError, "must not be later"):
            build_jql("SAM1", updated_from=date(2026, 11, 2), updated_through=date(2026, 11, 1))


class ValidateJiraIssueExportTests(unittest.TestCase):
    def _issue(self, points):
        return {
            "key": "SAM1-1",
            "fields": {
                "project": {"key": "SAM1"},
                "status": {
                    "name": "Done",
                    "statusCategory": {"name": "Done"},
                },
                "updated": "2026-11-20T12:00:00+00:00",
                "customfield_10016": points,
            },
        }

    def test_missing_or_invalid_points_make_the_total_unavailable(self):
        result = validate_issues(
            {"issues": [self._issue(3), self._issue(-1), self._issue(None)]},
            "SAM1",
            "customfield_10016",
        )
        self.assertEqual(result["issue_count"], 3)
        self.assertIsNone(result["story_points_total"])
        self.assertEqual(result["story_points_status"], "unavailable")
        self.assertEqual(len(result["warnings"]), 2)

    def test_rejects_issues_from_an_unexpected_project(self):
        issue = self._issue(2)
        issue["fields"]["project"]["key"] = "OTHER"
        result = validate_issues([issue], "SAM1", "customfield_10016")
        self.assertEqual(result["structurally_valid_issue_count"], 0)
        self.assertIsNone(result["story_points_total"])
        self.assertEqual(result["story_points_status"], "unavailable")
        self.assertTrue(any("does not match" in error for error in result["errors"]))

    def test_reports_total_when_all_story_point_values_are_valid(self):
        result = validate_issues(
            [self._issue(3), self._issue(2.5)],
            "SAM1",
            "customfield_10016",
        )
        self.assertEqual(result["story_points_total"], 5.5)
        self.assertEqual(result["story_points_status"], "available")


if __name__ == "__main__":
    unittest.main()
