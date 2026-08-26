import json
import unittest
from pathlib import Path
from unittest import mock

from email_intel.ai_review import _attachment_digest, _bound_body, _extract_group
from email_intel.parse import Email


class FakeBackend:
    def __init__(self, payload=None, fail=False):
        self.payload = payload or {"items": [], "meetings": []}
        self.fail = fail
        self.prompts = []
        self.images = []

    def complete(self, prompt, workspace, *, schema=None, timeout=600, images=None):
        self.prompts.append(prompt)
        self.images.extend(images or [])
        if self.fail:
            raise RuntimeError("boom")
        return json.dumps(self.payload, ensure_ascii=False)


class AiReviewTests(unittest.TestCase):
    def test_extract_failure_is_reported_per_email(self):
        email = Email(folder="e1", path="/tmp/e1", subject="S",
                      body_text="x" * 300, message_id="e1")
        backend = FakeBackend(fail=True)
        with mock.patch("email_intel.ai_review._review_backend", return_value=backend):
            result = _extract_group([email], Path("."))
        self.assertTrue(result["status"]["e1"].startswith("extract_failed"))
        self.assertEqual(result["items"], [])
        self.assertEqual(result["meetings"], [])

    def test_extract_passes_images_and_attachment_digest(self):
        email = Email(folder="e1", path="/tmp/e1", subject="S",
                      body_text="x" * 300, message_id="e1",
                      images=[("a.png", r"C:\tmp\a.png")],
                      pdfs=[("r.pdf", r"C:\tmp\r.pdf")],
                      attachments=[("x.xlsx", r"C:\tmp\x.xlsx")])
        backend = FakeBackend(payload={"items": [{"kind": "company_update", "company": "Co"}], "meetings": []})
        with mock.patch("email_intel.ai_review._review_backend", return_value=backend), \
             mock.patch("email_intel.ai_review._preview_pdfs", return_value={"e1": "pdf digest body"}):
            result = _extract_group([email], Path("."))
        self.assertEqual(result["status"]["e1"], "ok")
        self.assertEqual(backend.images, [r"C:\tmp\a.png"])
        prompt = backend.prompts[0]
        self.assertIn("pdf digest body", prompt)
        self.assertIn("PDF 附件文件名：r.pdf", prompt)
        self.assertIn("其他附件文件名", prompt)

    def test_bound_body_keeps_tail(self):
        body = "H" * 9_000 + "T" * 8_990 + "\nREGISTER https://example.com/join\n"
        bounded = _bound_body(body, max_chars=12_000)
        self.assertLessEqual(len(bounded), 12_000)
        self.assertIn("https://example.com/join", bounded)
        self.assertIn("中段省略", bounded)

    def test_attachment_digest_degrades_to_filenames(self):
        email = Email(folder="e1", path="/tmp/e1", message_id="e1",
                      pdfs=[("r.pdf", r"C:\tmp\r.pdf")])
        with mock.patch("email_intel.ai_review._preview_pdfs", return_value={}):
            digest = _attachment_digest([email], Path("."))
        self.assertIn("PDF 读取失败，仅保留文件名", digest["e1"])
