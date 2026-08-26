from __future__ import annotations

import unittest
from unittest.mock import patch

from email_intel.review_backend import CodexBackend, ReviewBackendError, backend_name


class ReviewBackendTests(unittest.TestCase):
    def test_codex_requires_chatgpt_login(self):
        backend = CodexBackend()
        with patch("email_intel.review_backend.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "Logged in using API key"
            with self.assertRaisesRegex(ReviewBackendError, "ChatGPT"):
                backend.check_auth()

    def test_default_backend_is_codex(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(backend_name(), "codex")
