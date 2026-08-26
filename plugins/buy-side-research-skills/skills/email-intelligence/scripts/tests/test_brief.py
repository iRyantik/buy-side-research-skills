import unittest

from email_intel import brief as brief_module
from email_intel.brief import _meeting_accent_v3, render_brief_html_v2, render_email_markdown, render_panel_html_v2
from email_intel.report import build_report
from email_intel.parse import Email


class BriefTests(unittest.TestCase):
    @staticmethod
    def _contrast(foreground, background):
        def luminance(color):
            channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
        lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
        return (lighter + 0.05) / (darker + 0.05)

    def test_brief_has_five_light_sections_and_multiple_meetings(self):
        email = Email(folder="e1", path="/tmp/e1", sender="Broker", outlook_link="https://example.com/e1")
        reviews = [{
        "_email_id": "e1",
        "items": [
            {"bucket": "core", "company": "CoreCo", "what_changed": "guidance up", "priority": "high"},
            {"bucket": "other_coverage", "company": "WatchCo", "what_changed": "margin down", "priority": "medium"},
            {"bucket": "new_idea", "company": "NewCo", "what_changed": "orders inflect", "priority": "high"},
            {"bucket": "industry_signal", "industry": "Defense", "what_changed": "budget expands", "priority": "medium"},
        ],
        "meetings": [
            {"title": "Company A meeting", "topic": "Demand", "recommendation": "high"},
            {"title": "Company B meeting", "topic": "Supply", "recommendation": "low"},
        ],
        }]
        output = render_brief_html_v2([email], reviews, "2026-08-24")
        for heading in ("Core Watch", "Other Coverage", "New Ideas", "Industry", "Meetings"):
            self.assertIn(heading, output)
        self.assertIn("Company A meeting", output)
        self.assertIn("Company B meeting", output)
        self.assertIn("https://example.com/e1", output)

    def test_report_merges_same_ticker_and_keeps_both_brokers(self):
        emails = [
            Email(folder="e1", path="/tmp/e1", sender="research@citi.com", outlook_link="https://example.com/citi"),
            Email(folder="e2", path="/tmp/e2", sender="research@ubs.com", outlook_link="https://example.com/ubs"),
        ]
        reviews = [
            {"_email_id": "e1", "items": [{"bucket": "other_coverage", "company": "Maxwell Technology", "ticker": "300751.SZ", "summary": "业绩披露", "broker": "Citi"}]},
            {"_email_id": "e2", "items": [{"bucket": "other_coverage", "company": "Maxwell Technology", "ticker": "300751.SZ", "summary": "半导体业务重要性提升", "broker": "UBS"}]},
        ]
        report = build_report(emails, reviews)
        self.assertEqual(len(report["items"]), 1)
        self.assertEqual(report["items"][0]["brokers"], ["Citi", "UBS"])
        self.assertEqual(len(report["items"][0]["facts"]), 2)

    def test_outlook_body_is_table_based_and_keeps_fixed_sections(self):
        email = Email(folder="e1", path="/tmp/e1", sender="research@cjsc.com.cn", outlook_link="https://example.com/e1")
        reviews = [{"_email_id": "e1", "items": [{
            "bucket": "industry_signal", "industry": "Semiconductor", "merge_key": "cloud-roic",
            "what_changed": "该事件在 system last_events 中已于 2026-08-24 出现过（CJSC-cloud-ROIC-analysis-2026-08-24），本次为同日报告正文解读，无新增事实。",
        }], "meetings": []}]
        output = render_brief_html_v2([email], reviews, "2026-08-26", last_events={
            "cloud-roic": {"what_changed": "云端光模块 ROIC 分析首次发布"}
        })
        for heading in ("01 · Worth Your Time", "02 · Industry", "03 · Core Watch", "04 · Other Coverage", "05 · New Ideas", "06 · Meetings"):
            self.assertIn(heading, output)
        self.assertIn("重复事件", output)
        self.assertIn("云端光模块 ROIC 分析首次发布", output)
        self.assertNotIn("system last_events", output)
        self.assertNotIn("CJSC-cloud-ROIC-analysis", output)
        self.assertNotIn("display:flex", output)
        self.assertNotIn("display:grid", output)
        self.assertIn("max-width:680px", output)

    def test_panel_long_meeting_title_has_own_row_and_no_four_column_grid(self):
        email = Email(folder="e1", path="/tmp/e1", sender="research@morganstanley.com", outlook_link="https://example.com/e1")
        title = "The Thematic Download: Perspectives from Asia & US Institutional Equities"
        reviews = [{"_email_id": "e1", "items": [], "meetings": [{
            "title": title, "industry": "Semiconductor", "date": "08-25", "time": "08:30 HKT",
            "broker": "Morgan Stanley", "recommendation": "recommend"
        }]}]
        output = render_panel_html_v2([email], reviews, "2026-08-26")
        self.assertIn(title.replace("&", "&amp;"), output)
        self.assertIn("meeting-title", output)
        self.assertNotIn("cols-4", output)
        self.assertNotIn("repeat(4", output)
        self.assertNotIn("&amp;amp;", output)

    def test_meeting_title_carries_registration_link_in_brief_panel_and_markdown(self):
        email = Email(folder="e1", path="/tmp/e1", sender="research@broker.com", outlook_link="https://example.com/email")
        registration = "https://example.com/register?event=semis&lang=zh"
        reviews = [{"_email_id": "e1", "items": [], "meetings": [{
            "title": "Semiconductor Equipment Group Call",
            "date": "2026-08-27",
            "time": "11:00 HKT",
            "registration": registration,
            "recommendation": "recommend",
        }]}]

        brief = render_brief_html_v2([email], reviews, "2026-08-26")
        panel = render_panel_html_v2([email], reviews, "2026-08-26")
        markdown = render_email_markdown([email], reviews, "2026-08-26")

        escaped = "https://example.com/register?event=semis&amp;lang=zh"
        self.assertIn(f"href='{escaped}'", brief)
        self.assertIn(f"href='{escaped}'", panel)
        linked_title = f"class='meeting-title-link' target='_blank' rel='noopener'>Semiconductor Equipment Group Call</a>"
        self.assertIn(linked_title, brief)
        self.assertIn(linked_title, panel)
        self.assertNotIn(">报名</a>", brief)
        self.assertNotIn(">报名</a>", panel)
        self.assertIn(f"[Semiconductor Equipment Group Call]({registration})", markdown)
        self.assertNotIn("报名：", markdown)

    def test_meetings_sort_by_attendability_recommendation_and_time(self):
        email = Email(folder="e1", path="/tmp/e1", sender="research@broker.com", outlook_link="https://example.com/email")
        meetings = [
            {"title": "Past Recommend", "date": "2026-08-25", "time": "09:00 HKT", "recommendation": "recommend"},
            {"title": "Unknown Date", "date": None, "time": "08:00 HKT", "recommendation": "recommend"},
            {"title": "Tomorrow Recommend", "date": "2026-08-27", "time": "08:00 HKT", "recommendation": "recommend"},
            {"title": "Today Consider", "date": "2026-08-26", "time": "09:00 HKT", "recommendation": "consider"},
            {"title": "Today Recommend Late", "date": "2026-08-26", "time": "15:00 HKT", "recommendation": "recommend"},
            {"title": "Today Recommend Early", "date": "2026-08-26", "time": "08:00 HKT", "recommendation": "recommend"},
            {"title": "Today Recommend TBD", "date": "2026-08-26", "time": "TBD", "recommendation": "recommend"},
        ]
        reviews = [{"_email_id": "e1", "items": [], "meetings": meetings}]

        panel = render_panel_html_v2([email], reviews, "2026-08-26 10:00 (+08:00)")
        brief = render_brief_html_v2([email], reviews, "2026-08-26 10:00 (+08:00)")
        expected = [
            "Today Recommend Early", "Today Recommend Late", "Today Recommend TBD",
            "Today Consider", "Tomorrow Recommend", "Unknown Date", "Past Recommend",
        ]
        for output in (brief, panel):
            positions = [output.index(title) for title in expected]
            self.assertEqual(positions, sorted(positions))

    def test_panel_meeting_heading_puts_broker_at_top_right(self):
        email = Email(folder="e1", path="/tmp/e1", sender="research@morganstanley.com", outlook_link="https://example.com/email")
        reviews = [{"_email_id": "e1", "items": [], "meetings": [{
            "title": "Compact Meeting", "date": "2026-08-27", "time": "11:00 HKT",
            "format": "Webinar", "language": "English", "recommendation": "recommend",
        }]}]
        panel = render_panel_html_v2([email], reviews, "2026-08-26")
        self.assertIn("class='meeting-heading'", panel)
        self.assertIn("class='meeting-broker'", panel)
        self.assertLess(panel.index("Compact Meeting"), panel.index("Morgan Stanley"))
        self.assertLess(panel.index("Morgan Stanley"), panel.index("2026-08-27 11:00 HKT · Webinar · English"))

    def test_action_is_not_rendered_in_brief_or_panel_cards(self):
        email = Email(folder="e1", path="/tmp/e1", sender="research@broker.com", outlook_link="https://example.com/email")
        reviews = [{"_email_id": "e1", "items": [{
            "bucket": "other_coverage",
            "company": "Example Co",
            "what_changed": "订单增长",
            "action": "add_to_watchlist",
        }], "meetings": []}]

        brief = render_brief_html_v2([email], reviews, "2026-08-26")
        panel = render_panel_html_v2([email], reviews, "2026-08-26")

        self.assertNotIn("动作：", brief)
        self.assertNotIn("加入关注", brief)
        self.assertNotIn("动作：", panel)
        self.assertNotIn("加入关注", panel)

    def test_company_status_and_core_badges_are_rendered(self):
        email = Email(folder="e1", path="/tmp/e1", sender="research@broker.com", outlook_link="https://example.com/email")
        reviews = [{"_email_id": "e1", "items": [
            {"bucket": "core", "company": "Core Co", "coverage_status": "Screened", "what_changed": "订单增长"},
            {"bucket": "other_coverage", "company": "Quick Co", "coverage_status": "Quickread", "what_changed": "利润改善"},
        ], "meetings": []}]

        brief = render_brief_html_v2([email], reviews, "2026-08-26")
        panel = render_panel_html_v2([email], reviews, "2026-08-26")

        for output in (brief, panel):
            self.assertIn("class='status-badge status-core'>Core</span>", output)
            self.assertIn("class='status-badge status-screened'>Screened</span>", output)
            self.assertIn("class='status-badge status-quickread'>Quickread</span>", output)

    def test_industry_card_separates_views_companies_and_uses_plain_title(self):
        email = Email(folder="e1", path="/tmp/e1", sender="research@ubs.com", outlook_link="https://example.com/email")
        reviews = [{"_email_id": "e1", "items": [
            {"bucket": "industry_signal", "industry": "Aerospace", "summary": "民航估值观点"},
            {"bucket": "industry_signal", "industry": "Aerospace", "company": "Melrose Industries", "ticker": "MRON.L", "summary": "Garden Grove 拨备更新"},
        ], "meetings": []}]

        brief = render_brief_html_v2([email], reviews, "2026-08-26")
        panel = render_panel_html_v2([email], reviews, "2026-08-26")

        for output in (brief, panel):
            self.assertIn("行业观点", output)
            self.assertIn("公司动态", output)
            self.assertIn("Melrose Industries", output)
            self.assertNotIn("行业面｜Aerospace", output)
            self.assertEqual(output.count("class='industry-company-name'"), 1)
        self.assertIn(">Aerospace</div>", panel)

    def test_industry_card_merges_space_and_hyphen_name_variants(self):
        email = Email(folder="e1", path="/tmp/e1", sender="research@ubs.com", outlook_link="https://example.com/email")
        reviews = [{"_email_id": "e1", "items": [
            {"bucket": "industry_signal", "industry": "Semiconductor Equipment", "summary": "设备需求改善"},
            {"bucket": "industry_signal", "industry": "Semiconductor-Equipment", "summary": "资本开支上调"},
        ], "meetings": [
            {"title": "Equipment Call One", "industry": "Semiconductor Equipment", "date": "2026-08-27", "recommendation": "recommend"},
            {"title": "Equipment Call Two", "industry": "Semiconductor-Equipment", "date": "2026-08-28", "recommendation": "recommend"},
        ]}]

        brief = render_brief_html_v2([email], reviews, "2026-08-26")
        panel = render_panel_html_v2([email], reviews, "2026-08-26")

        for output in (brief, panel):
            self.assertIn("设备需求改善", output)
            self.assertIn("资本开支上调", output)
        self.assertEqual(brief.count("background:#EDF4F7;border-left:4px solid #2F6B8A"), 1)
        self.assertEqual(panel.count("class='group-label'"), 1)
        self.assertEqual(
            panel.count("data-filter='Semiconductor Equipment'")
            + panel.count("data-filter='Semiconductor-Equipment'"),
            1,
        )

    def test_cards_show_all_matching_future_recommended_meetings(self):
        email = Email(folder="e1", path="/tmp/e1", sender="research@ubs.com", outlook_link="https://example.com/email")
        reviews = [{"_email_id": "e1", "items": [
            {"bucket": "industry_signal", "industry": "Aerospace", "summary": "行业更新"},
            {"bucket": "core", "company": "Howmet Aerospace", "ticker": "HWM.US", "summary": "公司更新"},
        ], "meetings": [
            {"title": "Aerospace Lunch One", "industry": "Aerospace & Defense", "date": "2026-08-27", "time": "09:00 HKT", "recommendation": "recommend"},
            {"title": "Aerospace Lunch Two", "industry": "Aerospace", "date": "2026-08-28", "time": "10:00 HKT", "recommendation": "high"},
            {"title": "Aerospace Lunch Three", "industry": "Aerospace", "date": "2026-08-29", "time": "11:00 HKT", "recommendation": "recommend"},
            {"title": "Howmet Call", "company": "Howmet Aerospace", "ticker": "HWM.US", "related_tickers": ["HWM.US"], "date": "2026-08-27", "time": "12:00 HKT", "recommendation": "recommend"},
            {"title": "Howmet Consider", "company": "Howmet Aerospace", "ticker": "HWM.US", "date": "2026-08-27", "time": "13:00 HKT", "recommendation": "consider"},
            {"title": "Past Aerospace", "industry": "Aerospace", "date": "2026-08-25", "time": "09:00 HKT", "recommendation": "recommend"},
        ]}]

        for output in (
            render_brief_html_v2([email], reviews, "2026-08-26"),
            render_panel_html_v2([email], reviews, "2026-08-26"),
        ):
            self.assertIn("related-meetings", output)
            for title in ("Aerospace Lunch One", "Aerospace Lunch Two", "Aerospace Lunch Three", "Howmet Call"):
                self.assertGreaterEqual(output.count(title), 2)
            self.assertEqual(output.count("Howmet Consider"), 1)
            self.assertEqual(output.count("Past Aerospace"), 1)

    def test_institutional_palette_separates_sections_status_and_meeting_priority(self):
        palette = getattr(brief_module, "_PALETTE_V3", {})
        expected = {
            "ink": "#172033", "muted": "#667085", "link": "#1D4ED8",
            "page_bg": "#EEF2F6", "card": "#FFFFFF", "border": "#D6DEE8",
            "worth": "#1E3A5F", "industry": "#2F6B8A", "core": "#6B5AA6",
            "other": "#667085", "ideas": "#0F766E", "meetings": "#4F46E5",
            "recommend": "#15803D", "consider": "#B54708", "skip": "#98A2B3",
        }
        self.assertEqual({key: palette.get(key) for key in expected}, expected)
        self.assertEqual(_meeting_accent_v3({"recommendation": "recommend"}), expected["recommend"])
        self.assertEqual(_meeting_accent_v3({"recommendation": "consider"}), expected["consider"])
        self.assertEqual(_meeting_accent_v3({"recommendation": "skip"}), expected["skip"])

        email = Email(folder="e1", path="/tmp/e1", sender="research@broker.com", outlook_link="https://example.com/email")
        reviews = [{"_email_id": "e1", "items": [
            {"bucket": "industry_signal", "industry": "Aerospace", "company": "Melrose", "summary": "行业公司变化"},
            {"bucket": "core", "company": "Core Co", "coverage_status": "Screened", "summary": "核心变化"},
            {"bucket": "other_coverage", "company": "Quick Co", "coverage_status": "Quickread", "summary": "覆盖变化"},
            {"bucket": "new_idea", "company": "Idea Co", "summary": "新想法"},
        ], "meetings": [
            {"title": "Recommend Call", "date": "2026-08-27", "recommendation": "recommend"},
            {"title": "Consider Call", "date": "2026-08-27", "recommendation": "consider"},
        ]}]
        brief = render_brief_html_v2([email], reviews, "2026-08-26")
        panel = render_panel_html_v2([email], reviews, "2026-08-26")

        for color in (expected["worth"], expected["industry"], expected["core"], expected["other"], expected["ideas"], expected["meetings"]):
            self.assertIn(color, brief)
            self.assertIn(color, panel)
        self.assertNotIn("#b7791f", brief.lower())
        self.assertNotIn("#b7791f", panel.lower())
        self.assertIn(f"color:{expected['other']}'>公司动态", brief)
        self.assertIn("style='color:#667085'>公司动态", panel)

        contrast_pairs = (
            ("ink", "card"), ("muted", "card"), ("link", "card"),
            ("recommend", "card"), ("consider", "card"),
            ("status_core_text", "status_core_bg"),
            ("status_screened_text", "status_screened_bg"),
            ("status_quickread_text", "status_quickread_bg"),
        )
        for foreground, background in contrast_pairs:
            self.assertGreaterEqual(self._contrast(palette[foreground], palette[background]), 4.5, f"{foreground} on {background}")
