from __future__ import annotations

import csv
import html
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from string import Template
from urllib.parse import urlparse

from openpyxl import load_workbook
from PIL import Image, ImageDraw, ImageFont

from referral import has_referral_signal


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ai-api-sites-table.xlsx"
SITE_URL = "https://bubblevv.github.io/ai-api-gongyi-nav/"
REPO_URL = "https://github.com/bubblevv/ai-api-gongyi-nav"
COVER_PATH = "assets/ai-api-gongyi-nav-cover.png"
TEMPLATE = Path(__file__).with_name("site_template.html")
OUTPUTS = {
    "index": ROOT / "index.html",
    "table_html": ROOT / "ai-api-sites-table.html",
    "share_html": ROOT / "ai-api-sites-share.html",
    "readme": ROOT / "README.md",
    "markdown": ROOT / "ai-api-sites-table.md",
    "csv": ROOT / "ai-api-sites-table.csv",
    "json": ROOT / "data" / "sites.json",
    "cover": ROOT / COVER_PATH,
    "robots": ROOT / "robots.txt",
    "sitemap": ROOT / "sitemap.xml",
}

KEYWORDS = [
    "ai api",
    "AI API",
    "AI API 公益站",
    "公益中转站",
    "公益 API",
    "AI API 中转站",
    "AI 中转站",
    "API 中转站",
    "GPT",
    "GPT API",
    "GPT API 免费",
    "OpenAI API",
    "OpenAI API 中转",
    "Claude",
    "Claude API",
    "Claude API 中转",
    "Codex",
    "Codex 编程",
    "DeepSeek",
    "DeepSeek API",
    "DeepSeek API 免费",
    "Gemini",
    "Gemini API",
    "GLM",
    "GLM API",
    "MiniMax",
    "New API",
    "New API 公益站",
    "ChatGPT API",
    "免费 AI API",
    "AI API 导航",
    "免费 API 额度",
    "API 签到额度",
    "编程",
    "编程 API",
    "龙虾",
    "酒馆",
    "酒馆 API",
]

FILTER_TAGS = ["公益", "Claude", "GPT", "DeepSeek", "Gemini", "Codex", "生图", "注册赠送", "签到"]


@dataclass(frozen=True)
class Site:
    index: int
    name: str
    url: str
    tags: tuple[str, ...]
    note: str
    added_date: str = ""

    @property
    def domain(self) -> str:
        host = urlparse(self.url).netloc
        return host.removeprefix("www.")

    @property
    def search_text(self) -> str:
        return " ".join([self.name, self.domain, self.note, self.added_date, *self.tags]).lower()


def text(value: object) -> str:
    return "" if value is None else str(value).strip()


def split_tags(raw: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in re.split(r"[;；]", raw) if part.strip())


def source_updated() -> str:
    mtime = datetime.fromtimestamp(SOURCE.stat().st_mtime)
    return mtime.strftime("%Y-%m-%d")


def normalize_added_date(value: object) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    raw = text(value)
    return date.fromisoformat(raw).isoformat() if raw else ""


def load_sites() -> tuple[str, str, list[Site]]:
    workbook = load_workbook(SOURCE, data_only=True)
    sheet = workbook.active
    heading = text(sheet.cell(row=1, column=1).value)
    heading_lines = [line.strip() for line in heading.splitlines() if line.strip()]
    title = heading_lines[0] if heading_lines else "AI API 公益中转站导航"
    subtitle = " ".join(heading_lines[1:])
    sites: list[Site] = []

    header_row = None
    for row_number in range(1, min(sheet.max_row, 10) + 1):
        headers = [text(sheet.cell(row=row_number, column=column).value) for column in range(1, 6)]
        if headers[:5] == ["序号", "站点", "链接", "标签", "备注"]:
            header_row = row_number
            break
    if header_row is None:
        raise ValueError("Could not find header row: 序号/站点/链接/标签/备注")

    for row in sheet.iter_rows(min_row=header_row + 1, values_only=True):
        if not any(row):
            continue
        index_raw, name_raw, url_raw, tags_raw, note_raw = row[:5]
        added_date_raw = row[5] if len(row) > 5 else ""
        name = text(name_raw)
        url = text(url_raw)
        if not name or not url:
            continue
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"Invalid URL for {name}: {url}")
        if not has_referral_signal(url):
            raise ValueError(f"Referral signal missing for {name}: {url}")
        sites.append(
            Site(
                index=int(index_raw),
                name=name,
                url=url,
                tags=split_tags(text(tags_raw)),
                note=text(note_raw),
                added_date=normalize_added_date(added_date_raw),
            )
        )

    # Dated entries lead, with larger IDs breaking same-day ties. Keep the
    # workbook's original numbering order for historical entries with no date.
    sites.sort(key=lambda site: (site.added_date, site.index if site.added_date else -site.index), reverse=True)
    return title, subtitle, sites


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def write_cover(title: str, sites: list[Site]) -> None:
    OUTPUTS["cover"].parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1200, 630), "#f2ecff")
    draw = ImageDraw.Draw(image)

    font_dir = Path("C:/Windows/Fonts")
    font_regular = font_dir / "msyh.ttc"
    font_bold = font_dir / "msyhbd.ttc"
    title_font = ImageFont.truetype(str(font_bold if font_bold.exists() else font_regular), 58)
    sub_font = ImageFont.truetype(str(font_regular), 28)
    card_font = ImageFont.truetype(str(font_regular), 23)
    small_font = ImageFont.truetype(str(font_regular), 20)

    draw.rectangle((0, 0, 1200, 630), fill="#f2ecff")
    draw.rectangle((0, 0, 1200, 19), fill="#542db3")
    draw.text((64, 78), title, fill="#211936", font=title_font)
    draw.text((68, 156), "GPT / Claude / Codex / DeepSeek / 免费额度 / API 中转", fill="#55496b", font=sub_font)
    draw.text((68, 207), f"收录 {len(sites)} 个 AI API 公益站和中转站入口", fill="#625976", font=small_font)

    columns = [(68, 284), (438, 284), (808, 284)]
    for idx, site in enumerate(sites[:9]):
        col_x, base_y = columns[idx % 3]
        y = base_y + (idx // 3) * 92
        draw.rounded_rectangle((col_x, y, col_x + 320, y + 64), radius=8, fill="#ffffff", outline="#e6e0f1", width=2)
        draw.rectangle((col_x, y, col_x + 7, y + 64), fill="#7d56d3")
        draw.text((col_x + 20, y + 10), site.name[:15], fill="#211936", font=card_font)
        draw.text((col_x + 20, y + 38), site.added_date or " / ".join(site.tags[:2]), fill="#625976", font=small_font)

    image.save(OUTPUTS["cover"], optimize=True)


def write_csv(sites: list[Site]) -> None:
    with OUTPUTS["csv"].open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["序号", "站点", "注册链接", "标签", "备注", "添加日期"])
        for site in sites:
            writer.writerow([site.index, site.name, site.url, ";".join(site.tags), site.note, site.added_date])


def site_to_dict(site: Site) -> dict[str, object]:
    return {
        "index": site.index,
        "name": site.name,
        "url": site.url,
        "domain": site.domain,
        "tags": list(site.tags),
        "note": site.note,
        "added_date": site.added_date,
    }


def write_json(title: str, subtitle: str, updated: str, sites: list[Site]) -> None:
    OUTPUTS["json"].parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "title": title,
        "description": subtitle,
        "updated": updated,
        "keywords": KEYWORDS,
        "sites": [site_to_dict(site) for site in sites],
    }
    OUTPUTS["json"].write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def markdown_link(site: Site) -> str:
    return f"[注册链接]({site.url})"


def write_markdown(title: str, subtitle: str, updated: str, sites: list[Site]) -> str:
    rows = [
        f"# {title}",
        "",
        f"> {subtitle}",
        "",
        f"更新日期：{updated}",
        "",
        "这里整理可用于编程、酒馆、龙虾和日常模型调用的 AI API 公益站与中转站入口，重点覆盖 GPT、Claude、DeepSeek、Gemini、GLM、MiniMax、Codex 等常见模型。",
        "",
        "使用前请自行确认额度、倍率、模型可用性和注册状态；不要上传隐私数据、密钥或敏感文件。本站只做导航收录，不对任何第三方站点的服务质量、稳定性或数据安全负责。",
        "",
        "| 序号 | 站点 | 注册链接 | 标签 | 备注 | 添加日期 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for site in sites:
        rows.append(
            f"| {site.index} | {site.name} | {markdown_link(site)} | {'; '.join(site.tags)} | {site.note} | {site.added_date} |"
        )
    content = "\n".join(rows) + "\n"
    readme_rows = rows[:4] + [f"[打开网页版 · 搜索和筛选全部站点]({SITE_URL})", ""] + rows[4:]
    OUTPUTS["readme"].write_text("\n".join(readme_rows) + "\n", encoding="utf-8")
    OUTPUTS["markdown"].write_text(content, encoding="utf-8")
    return content


def card_html(site: Site) -> str:
    tags = "".join(f'<li class="tag">{esc(tag)}</li>' for tag in site.tags)
    tag_list = f'\n          <ul class="tags" aria-label="站点标签">{tags}</ul>' if tags else ""
    added_date = (
        f'\n            <time datetime="{esc(site.added_date)}">{esc(site.added_date)}</time>' if site.added_date else ""
    )
    tone = ("violet", "teal", "berry")[site.index % 3]
    return f"""
        <article class="site-card" id="site-{site.index}" data-search="{esc(site.search_text)}">
          <div class="card-head">
            <span class="site-mark {tone}" aria-hidden="true">{esc(site.name[0].upper())}</span>
            <div class="site-identity">
              <h4>{esc(site.name)}</h4>
            </div>
          </div>{tag_list}
          <p class="note">{esc(site.note)}</p>
          <div class="card-foot">{added_date}
            <a class="visit" href="{esc(site.url)}" target="_blank" rel="sponsored noopener noreferrer" aria-label="注册链接 · {esc(site.name)}">注册链接 <span aria-hidden="true">↗</span></a>
          </div>
        </article>"""


def section_html(section_id: str, heading: str, sites: list[Site], note: str) -> str:
    if not sites:
        return ""
    cards = "\n".join(card_html(site) for site in sites)
    return f"""
    <section class="site-section" id="{section_id}" aria-labelledby="{section_id}-heading">
      <h3 id="{section_id}-heading">{esc(heading)}</h3>
      <p class="section-note">{esc(note)}</p>
      <div class="grid">{cards}
      </div>
    </section>"""


def write_html(title: str, subtitle: str, updated: str, sites: list[Site]) -> str:
    description = (
        "AI API 公益站和中转站导航，按添加日期整理 GPT、Claude、DeepSeek、Gemini、"
        "GLM、MiniMax、Codex 和 New API 等入口，支持按站名、模型和标签筛选。"
    )
    filter_tags = [tag for tag in FILTER_TAGS if any(tag in site.tags for site in sites)]
    filters = "".join(
        f'\n          <button class="filter" type="button" data-filter="{esc(tag)}" aria-pressed="false">{esc(tag)}</button>'
        for tag in filter_tags
    )
    dated = [site for site in sites if site.added_date]
    archive = [site for site in sites if not site.added_date]
    json_ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": description,
        "url": SITE_URL,
        "dateModified": updated,
        "inLanguage": "zh-CN",
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(sites),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": position,
                    "name": site.name,
                    "url": f"{SITE_URL}#site-{site.index}",
                }
                for position, site in enumerate(sites, start=1)
            ],
        },
    }
    html_doc = Template(TEMPLATE.read_text(encoding="utf-8")).substitute(
        title=esc(title),
        subtitle=esc(subtitle or description),
        description=esc(description),
        site_url=esc(SITE_URL),
        repo_url=esc(REPO_URL),
        cover_url=esc(SITE_URL + COVER_PATH),
        json_ld=json.dumps(json_ld, ensure_ascii=False).replace("<", "\\u003c"),
        count=len(sites),
        updated=esc(updated),
        filters=filters,
        dated_section=section_html("recent", "最新收录", dated, "按添加日期倒序"),
        archive_section=section_html("archive", "早期收录", archive, "未记录添加日期"),
    )
    for key in ("index", "table_html", "share_html"):
        OUTPUTS[key].write_text(html_doc, encoding="utf-8")
    return html_doc


def write_search_files(updated: str) -> None:
    OUTPUTS["robots"].write_text(
        "\n".join(
            [
                "User-agent: *",
                "Allow: /",
                f"Sitemap: {SITE_URL}sitemap.xml",
                "",
            ]
        ),
        encoding="utf-8",
    )
    OUTPUTS["sitemap"].write_text(
        "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
                "  <url>",
                f"    <loc>{esc(SITE_URL)}</loc>",
                f"    <lastmod>{esc(updated)}</lastmod>",
                "  </url>",
                "</urlset>",
                "",
            ]
        ),
        encoding="utf-8",
    )


def verify_links(html_doc: str, markdown_doc: str, sites: list[Site]) -> None:
    allowed = {site.url for site in sites}
    allowed_hrefs = allowed | {SITE_URL, REPO_URL}
    hrefs = {html.unescape(href) for href in re.findall(r'href="([^"]+)"', html_doc)}
    md_links = set(re.findall(r"\]\((https?://[^)]+)\)", markdown_doc))
    bad_hrefs = sorted(href for href in hrefs if href.startswith(("http://", "https://")) and href not in allowed_hrefs)
    bad_md = sorted(link for link in md_links if link not in allowed)
    if bad_hrefs or bad_md:
        raise ValueError(f"Unexpected non-aff links: html={bad_hrefs}, markdown={bad_md}")


def main() -> None:
    title, subtitle, sites = load_sites()
    updated = source_updated()
    write_cover(title, sites)
    write_csv(sites)
    write_json(title, subtitle, updated, sites)
    markdown_doc = write_markdown(title, subtitle, updated, sites)
    html_doc = write_html(title, subtitle, updated, sites)
    write_search_files(updated)
    verify_links(html_doc, markdown_doc, sites)
    print(f"Generated {len(sites)} sites from {SOURCE.name}")


if __name__ == "__main__":
    main()
