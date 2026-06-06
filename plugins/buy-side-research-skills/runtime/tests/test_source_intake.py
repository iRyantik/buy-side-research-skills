import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from buy_side_research_runtime.source_intake import IntakeRequest, SourceIntake
from buy_side_research_runtime.source_intake.converters import convert_source


class SourceIntakeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.intake = SourceIntake(self.workspace)

    def tearDown(self):
        self.temp.cleanup()

    def test_explicit_route_preserves_user_source_and_publishes_mirrored_paths(self):
        source = self.workspace / "report.txt"
        source.write_text("Revenue increased 20%.", encoding="utf-8")

        result = self.intake.add(
            IntakeRequest(source=source, topic="industry/test/companies/acme", category="sell-side")
        )

        self.assertEqual("published", result.status)
        self.assertTrue(source.exists())
        self.assertTrue(Path(result.raw_path).exists())
        self.assertTrue(Path(result.cache_path).exists())
        manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
        self.assertEqual(result.source_id, manifest["source_id"])
        self.assertEqual("sell-side", manifest["route"]["category"])

    def test_low_confidence_route_is_quarantined_not_published(self):
        source = self.workspace / "unknown.txt"
        source.write_text("Unclassified research note.", encoding="utf-8")

        result = self.intake.add(IntakeRequest(source=source))

        self.assertEqual("quarantined", result.status)
        self.assertIn("_inbox", result.raw_path)
        self.assertIn("_quarantine", result.raw_path)
        self.assertFalse(any(self.workspace.glob("industry/**/_cache/**/document.md")))

    def test_content_hash_deduplicates_same_source(self):
        first = self.workspace / "a.txt"
        second = self.workspace / "b.txt"
        first.write_text("same body", encoding="utf-8")
        second.write_text("same body", encoding="utf-8")
        request = {"topic": "industry/test", "category": "institution"}

        one = self.intake.add(IntakeRequest(source=first, **request))
        two = self.intake.add(IntakeRequest(source=second, **request))

        self.assertEqual(one.source_id, two.source_id)
        self.assertEqual("duplicate", two.status)
        self.assertTrue(second.exists())

    def test_reproducible_source_deleted_only_after_validated_publish(self):
        source = self.workspace / "download.txt"
        source.write_text("downloaded body", encoding="utf-8")

        result = self.intake.add(
            IntakeRequest(
                source=source,
                topic="industry/test",
                category="web",
                source_url="https://example.com/report.txt",
                reproducible=True,
            )
        )

        self.assertEqual("published", result.status)
        self.assertFalse(source.exists())
        self.assertTrue(Path(result.raw_path).exists())
        self.assertTrue(Path(result.cache_path).read_text(encoding="utf-8").strip())

    def test_scan_is_not_recursive_by_default(self):
        inbox = self.workspace / "_inbox"
        nested = inbox / "nested"
        nested.mkdir(parents=True)
        (inbox / "top.txt").write_text("top", encoding="utf-8")
        (nested / "nested.txt").write_text("nested", encoding="utf-8")

        results = self.intake.scan(inbox)

        self.assertEqual(1, len(results))
        self.assertEqual("top.txt", Path(results[0].original_path).name)

    def test_office_open_xml_converters_are_pure_and_dependency_free(self):
        docx = self.workspace / "report.docx"
        pptx = self.workspace / "deck.pptx"
        xlsx = self.workspace / "model.xlsx"
        with zipfile.ZipFile(docx, "w") as archive:
            archive.writestr(
                "word/document.xml",
                '<w:document xmlns:w="w"><w:body><w:p><w:r><w:t>Doc text</w:t></w:r></w:p></w:body></w:document>',
            )
        with zipfile.ZipFile(pptx, "w") as archive:
            archive.writestr(
                "ppt/slides/slide1.xml",
                '<p:sld xmlns:p="p" xmlns:a="a"><a:t>Slide text</a:t></p:sld>',
            )
        with zipfile.ZipFile(xlsx, "w") as archive:
            archive.writestr(
                "xl/worksheets/sheet1.xml",
                '<worksheet xmlns="x"><sheetData><row><c t="inlineStr"><is><t>Cell text</t></is></c></row></sheetData></worksheet>',
            )

        self.assertIn("Doc text", convert_source(docx).markdown)
        self.assertIn("Slide text", convert_source(pptx).markdown)
        self.assertIn("Cell text", convert_source(xlsx).markdown)
        self.assertTrue(docx.exists())
        self.assertTrue(pptx.exists())
        self.assertTrue(xlsx.exists())


if __name__ == "__main__":
    unittest.main()
