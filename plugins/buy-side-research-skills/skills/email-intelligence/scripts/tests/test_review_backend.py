from __future__ import annotations

import unittest
from unittest.mock import patch

from email_intel.review_backend import CodexBackend, ReviewBackendError, backend_name


class ReviewBackendTests(unittest.TestCase):
    def test_codex_accepts_chatgpt_or_api_key_login(self):
        backend = CodexBackend()
        with patch("email_intel.review_backend.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "Logged in using API key"
            run.return_value.stderr = ""
            backend.check_auth()  # should NOT raise
        with patch("email_intel.review_backend.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "Logged in using ChatGPT"
            run.return_value.stderr = ""
            backend.check_auth()  # should NOT raise

    def test_codex_rejects_not_logged_in(self):
        backend = CodexBackend()
        with patch("email_intel.review_backend.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "Log in to use Codex"
            run.return_value.stderr = ""
            with self.assertRaisesRegex(ReviewBackendError, "未登录"):
                backend.check_auth()

    def test_default_backend_is_codex(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(backend_name(), "codex")
