"""Regression tests for GitHub REST/search rate control, no live requests."""
from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import sys
import unittest
import urllib.error
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/github_lifetime_audit.py"
spec = importlib.util.spec_from_file_location("github_lifetime_audit_rate_test", SCRIPT)
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


class Clock:
    def __init__(self):
        self.now = 100.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def time(self):
        return 1700000000 + self.now

    def sleep(self, amount):
        self.sleeps.append(amount)
        self.now += amount


class Reply(io.BytesIO):
    def __init__(self, body=b'{"ok":true}', headers=None):
        super().__init__(body)
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def error(code, headers=None, message="API rate limit exceeded"):
    return urllib.error.HTTPError(
        "https://api.github.com/search/commits", code, "error",
        headers or {}, io.BytesIO(('{"message":"' + message + '"}').encode())
    )


class RateLimitTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.api = audit.GitHubAPI("fake_token_only_for_tests")
        self.patchers = [
            patch.object(audit.time, "monotonic", self.clock.monotonic),
            patch.object(audit.time, "time", self.clock.time),
            patch.object(audit.time, "sleep", self.clock.sleep),
        ]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_search_is_serialized_and_paced_before_limit(self):
        with patch.object(audit.urllib.request, "urlopen",
                          side_effect=[Reply(), Reply(), Reply()]) as do:
            self.assertTrue(self.api.request("/search/commits")["ok"])
            self.assertTrue(self.api.request("/search/issues")["ok"])
            self.assertTrue(self.api.request("/user")["ok"])
        self.assertEqual(do.call_count, 3)
        self.assertGreaterEqual(self.clock.now, 105.0)
        self.assertGreaterEqual(sum(self.clock.sleeps), 5)
        self.assertIsNotNone(self.api._lock)

    def test_secondary_retry_after_obeyed(self):
        with patch.object(audit.urllib.request, "urlopen",
                          side_effect=[error(403, {"Retry-After": "33"},
                            "You have exceeded a secondary rate limit."),
                                       Reply()]) as do:
            response = self.api.request("/search/commits", {"q":"author:christo"})
        self.assertTrue(response["ok"])
        self.assertEqual(do.call_count, 2)
        self.assertGreaterEqual(sum(self.clock.sleeps), 33)

    def test_secondary_without_headers_waits_minimum_one_minute(self):
        exc = error(403, {}, "You have exceeded a secondary rate limit.")
        self.assertGreaterEqual(self.api._rate_limit_pause(
            exc, 0, '{"message":"secondary rate limit"}'), 60)

    def test_primary_limit_obeys_epoch_reset(self):
        exc = error(403, {"X-RateLimit-Remaining":"0",
                          "X-RateLimit-Reset":str(int(self.clock.time())+90)})
        self.assertGreaterEqual(self.api._rate_limit_pause(exc, 0, ""), 90)

    def test_unrelated_permission_403_never_retried(self):
        with patch.object(audit.urllib.request, "urlopen",
                          side_effect=error(403, {},
                            "Resource not accessible by personal access token")) as do:
            with self.assertRaisesRegex(audit.APIError, "HTTP 403"):
                self.api.request("/repos/me/inaccessible")
        self.assertEqual(do.call_count, 1)

    def test_optional_rate_limit_is_not_silently_ignored(self):
        with patch.object(audit.urllib.request, "urlopen",
                          side_effect=[
                            error(403, {"Retry-After":"4"}, "Secondary rate limit exceeded"),
                            Reply()
                          ]) as do:
            self.assertEqual(
                self.api.request("/repos/me/fork", optional=True),
                {"ok":True})
        self.assertEqual(do.call_count, 2)

    def test_optional_permission_forbidden_still_returns_none(self):
        with patch.object(audit.urllib.request, "urlopen",
                          side_effect=error(403, {}, "Resource not accessible")) as do:
            self.assertIsNone(self.api.request("/user/emails", optional=True))
        self.assertEqual(do.call_count, 1)

    def test_retries_eventually_fail_safely(self):
        def always_throttled(*_args, **_kwargs):
            raise error(429, {"Retry-After":"1"}, "rate limit exceeded")
        with patch.object(audit.urllib.request, "urlopen",
                          side_effect=always_throttled) as do:
            with self.assertRaisesRegex(audit.APIError, "rate limit still blocked"):
                self.api.request("/search/commits", {"q":"author:christo"})
        self.assertEqual(do.call_count, 7)


if __name__ == "__main__":
    unittest.main()
