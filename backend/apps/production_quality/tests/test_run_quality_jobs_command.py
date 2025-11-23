from __future__ import annotations

from unittest import mock

from django.core.management import call_command
from django.test import TestCase


class RunQualityJobsCommandTests(TestCase):
    @mock.patch("backend.apps.production_quality.management.commands.run_quality_jobs.call_command")
    def test_default_runs_global_and_alerts(self, mock_call_command):
        call_command("run_quality_jobs")

        mock_call_command.assert_any_call("capture_opinion_stats", type="quality")
        mock_call_command.assert_any_call("issue_quality_alerts")
        self.assertEqual(mock_call_command.call_count, 2)

    @mock.patch("backend.apps.production_quality.management.commands.run_quality_jobs.call_command")
    def test_projects_and_skip_alerts(self, mock_call_command):
        call_command("run_quality_jobs", project=[11, 22], stat_type="quality", skip_alerts=True)

        expected_calls = [
            mock.call("capture_opinion_stats", type="quality"),
            mock.call("capture_opinion_stats", type="quality", project=11),
            mock.call("capture_opinion_stats", type="quality", project=22),
        ]
        mock_call_command.assert_has_calls(expected_calls)
        self.assertEqual(mock_call_command.call_count, len(expected_calls))
