from __future__ import annotations

import tempfile
import json
import re
import unittest
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import generate_site


class LoadSitesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_source = generate_site.SOURCE
        self.original_outputs = generate_site.OUTPUTS.copy()

    def tearDown(self) -> None:
        generate_site.SOURCE = self.original_source
        generate_site.OUTPUTS.clear()
        generate_site.OUTPUTS.update(self.original_outputs)

    def write_workbook(self, headers: list[str], *rows: list[object]) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "sites.xlsx"
        workbook = Workbook()
        sheet = workbook.active
        sheet.cell(row=1, column=1).value = "公益站导航\n测试说明"
        for column, header in enumerate(headers, start=1):
            sheet.cell(row=2, column=column).value = header
        for row in rows:
            sheet.append(row)
        workbook.save(path)
        return path

    def test_load_sites_reads_added_date_column(self) -> None:
        generate_site.SOURCE = self.write_workbook(
            ["序号", "站点", "链接", "标签", "备注", "添加日期"],
            [1, "J3GB", "https://vip.j3gb.com/register?aff=KEHXUQAGYBF8", "公益;注册赠送", "注册送15刀", "2026-07-01"],
        )

        _, _, sites = generate_site.load_sites()

        self.assertEqual(sites[0].added_date, "2026-07-01")
        self.assertEqual(generate_site.site_to_dict(sites[0])["added_date"], "2026-07-01")

    def test_load_sites_sorts_by_date_then_id_and_keeps_undated_entries_last(self) -> None:
        url = "https://example.com/register?aff=abc"
        generate_site.SOURCE = self.write_workbook(
            ["序号", "站点", "链接", "标签", "备注", "添加日期"],
            [30, "older", url, "", "", "2026-07-01"],
            [1, "archive", url, "", ""],
            [31, "newest", url, "", "", datetime(2026, 7, 16)],
            [29, "earlier-addition", url, "", "", "2026-07-16"],
            [2, "later-archive", url, "", ""],
        )

        _, _, sites = generate_site.load_sites()

        self.assertEqual([site.index for site in sites], [31, 29, 30, 1, 2])
        self.assertEqual(sites[0].added_date, "2026-07-16")

    def test_load_sites_keeps_old_five_column_workbooks_compatible(self) -> None:
        generate_site.SOURCE = self.write_workbook(
            ["序号", "站点", "链接", "标签", "备注"],
            [1, "Old", "https://old.example.com/register?aff=abc", "公益", "旧格式"],
        )

        _, _, sites = generate_site.load_sites()

        self.assertEqual(sites[0].added_date, "")

    def test_load_sites_accepts_referral_ref_query(self) -> None:
        generate_site.SOURCE = self.write_workbook(
            ["序号", "站点", "链接", "标签", "备注", "添加日期"],
            [
                1,
                "0d0d",
                "https://ai.0d0d.top/register?ref=ioc8gkzq",
                "公益;国模",
                "邀请码注册送20刀",
                "2026-07-06",
            ],
        )

        _, _, sites = generate_site.load_sites()

        self.assertEqual(sites[0].url, "https://ai.0d0d.top/register?ref=ioc8gkzq")

    def test_static_pages_preserve_links_order_and_escape_untrusted_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            for key in ("index", "table_html", "share_html"):
                generate_site.OUTPUTS[key] = Path(temp_dir) / (key + ".html")
            site = generate_site.Site(
                55, '站点 </script><script>alert(1)</script>',
                'https://example.com/register?aff=abc&source=nav',
                ('公益',), '<img src=x onerror=alert(1)>', '2026-11-19',
            )
            archive = generate_site.Site(1, '旧站', 'https://old.example.com/?ref=x', (), '历史收录')

            content = generate_site.write_html('导航', '说明', '2026-11-19', [site, archive])
            generate_site.verify_links(content, generate_site.markdown_link(site), [site, archive])

            for key in ("index", "table_html", "share_html"):
                self.assertEqual(generate_site.OUTPUTS[key].read_text(encoding='utf-8'), content)
            self.assertLess(content.index('id="site-55"'), content.index('id="site-1"'))
            self.assertIn('href="https://example.com/register?aff=abc&amp;source=nav"', content)
            self.assertIn('&lt;img src=x onerror=alert(1)&gt;', content)
            self.assertNotIn('<img src=x', content)
            self.assertEqual(content.count('class="site-card"'), 2)
            self.assertNotIn('class="domain"', content)
            self.assertNotIn('推广链接', content)
            self.assertNotIn('专属链接', content)
            self.assertEqual(content.count('aria-label="注册链接 · '), 2)
            self.assertIn('property="og:image" content="' + generate_site.SITE_URL, content)
            raw_ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', content).group(1)
            items = json.loads(raw_ld)['mainEntity']['itemListElement']
            self.assertEqual(items[0]['name'], site.name)
            self.assertEqual(items[0]['url'], generate_site.SITE_URL + '#site-55')
            self.assertEqual([item['position'] for item in items], [1, 2])
            self.assertNotIn('</script>', raw_ld)

    def test_write_markdown_omits_generated_file_manifest(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        output_dir = Path(temp_dir.name)
        generate_site.OUTPUTS["readme"] = output_dir / "README.md"
        generate_site.OUTPUTS["markdown"] = output_dir / "sites.md"
        site = generate_site.Site(
            index=1,
            name="JianZhiLe",
            url="https://jianzhile.vip/register?aff=iszB",
            tags=("签到", "GPT"),
            note="【0706新增】注册20刀，签到20刀",
            added_date="2026-07-06",
        )

        content = generate_site.write_markdown("公益站导航", "测试说明", "2026-07-06", [site])

        self.assertIn("JianZhiLe", content)
        self.assertIn("添加日期", content)
        self.assertIn("| 站点 | 注册链接 |", content)
        self.assertIn("[注册链接](" + site.url + ")", content)
        self.assertNotIn("专属链接", content)
        self.assertNotIn("## 文件", content)
        self.assertNotIn("`index.html`", content)
        self.assertNotIn("tools/generate_site.py", content)


if __name__ == "__main__":
    unittest.main()
