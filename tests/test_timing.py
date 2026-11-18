from pathlib import Path
import json
import subprocess
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / ".agents/skills/momo-timing/scripts"
sys.path.insert(0, str(SCRIPTS))
from timing import activation, guard


class TriggerTests(unittest.TestCase):
    def test_bare_command(self):
        self.assertEqual(activation(" timing\n"), {"triggered": True, "task": None})

    def test_task_delimiters(self):
        for delimiter in (" ", "\n", ":", "：", " : "):
            with self.subTest(delimiter=delimiter):
                self.assertEqual(
                    activation(f"timing{delimiter}检查图纸"),
                    {"triggered": True, "task": "检查图纸"},
                )

    def test_false_triggers(self):
        for message in (
            "", "Timing", "timing-report", "timings", "什么是 timing？",
            "`timing`", "\"timing\"", "> timing", "```\ntiming\n```", "$momo-timing",
        ):
            with self.subTest(message=message):
                self.assertFalse(activation(message)["triggered"])

    def test_utf8_stdin(self):
        run = subprocess.run(
            [sys.executable, str(SCRIPTS / "timing.py"), "trigger"],
            input="timing：检查文件".encode("utf-8"),
            capture_output=True,
            check=True,
        )
        self.assertEqual(json.loads(run.stdout)["task"], "检查文件")


class GuardTests(unittest.TestCase):
    def check(self, **changes):
        data = {
            "now": "2026-11-18T16:30:00+08:00",
            "started_at": "2026-11-18T16:00:00+08:00",
            "minutes": 60,
            "reserve_percent": 20,
            "usage_allowed": True,
            "windows": {"5h": 35, "weekly": 55},
        }
        return guard(data | changes)

    def test_remaining_time_and_quota(self):
        self.assertEqual(self.check(), {
            "deadline": "2026-11-18T17:00:00+08:00",
            "seconds_left": 1800,
            "remaining_percent": {"5h": 65, "weekly": 45},
            "status": "within_bounds",
        })

    def test_absolute_deadline_and_equivalent_timezones(self):
        result = guard({
            "now": "2026-11-18T09:00:00+00:00",
            "deadline": "2026-11-18T17:00:00+08:00",
            "reserve_percent": 20,
            "windows": {"5h": 50},
        })
        self.assertEqual(result["status"], "deadline")
        self.assertEqual(result["seconds_left"], 0)

    def test_expired_deadline(self):
        self.assertEqual(self.check(now="2026-11-18T17:05:00+08:00")["seconds_left"], 0)

    def test_reserve_applies_to_each_window_at_equality(self):
        for name in ("5h", "weekly"):
            with self.subTest(window=name):
                self.assertEqual(self.check(windows={"5h": 0, "weekly": 0, name: 80})["status"], "reserve")

    def test_unknown_is_distinct_from_empty_balance(self):
        for windows in ({}, {"weekly": None}, {"5h": 42, "weekly": None}):
            with self.subTest(windows=windows):
                self.assertEqual(self.check(windows=windows)["status"], "unknown")
        self.assertEqual(self.check(windows={"weekly": 100})["status"], "reserve")

    def test_unknown_window_does_not_override_known_reserve(self):
        self.assertEqual(self.check(windows={"5h": None, "weekly": 85})["status"], "reserve")

    def test_account_disallows_work_even_when_balances_look_healthy(self):
        self.assertEqual(self.check(usage_allowed=False)["status"], "usage_unavailable")

    def test_bad_numbers_or_conflicting_time_fields(self):
        for changes in (
            {"minutes": 0}, {"minutes": -1}, {"minutes": True},
            {"minutes": float("inf")}, {"reserve_percent": 101},
            {"windows": {"weekly": -2}}, {"usage_allowed": "false"},
            {"deadline": "2026-11-18T17:00:00+08:00"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.check(**changes)

    def test_bad_clock_inputs(self):
        for now in ("2026-11-18T16:30:00", "2026-11-18T15:59:59+08:00"):
            with self.subTest(now=now), self.assertRaises(ValueError):
                self.check(now=now)


if __name__ == "__main__":
    unittest.main()
