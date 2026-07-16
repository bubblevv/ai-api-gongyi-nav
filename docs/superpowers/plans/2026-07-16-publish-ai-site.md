# Publish AI Site Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repository-specific Codex skill that turns a promotional-site text into a validated workbook entry, regenerated site files, a Git commit, and a push to the current branch.

**Architecture:** Keep parsing, workbook mutation, generated-file regeneration, and release-path selection in `tools/publish_site.py`; keep Git commit and push operations in the project skill so diagnostic runs never publish. The skill accepts a promotional copy file, invokes the tool in dry-run and write modes, validates the result, and stages only the fixed release allowlist.

**Tech Stack:** Python 3, `openpyxl`, `unittest`, existing `tools/generate_site.py`, Git, Agent Skills Markdown.

---

## File Structure

- Create: `.agents/skills/publish-ai-site/SKILL.md` - repository-specific publication workflow and Git safety rules.
- Create: `.agents/skills/publish-ai-site/agents/openai.yaml` - skill selector metadata.
- Create: `tools/publish_site.py` - deterministic parser, validator, workbook updater, site generator launcher, and release-path provider.
- Create: `tests/test_publish_site.py` - unit and filesystem-integration tests for the publisher.
- Modify: `.gitignore` - exclude temporary promotional-copy files if the tool uses a project-local temporary directory; otherwise leave unchanged.

### Task 1: Define Publisher Behavior With Failing Tests

**Files:**
- Create: `tests/test_publish_site.py`
- Create: `tools/publish_site.py` (empty module only, after the first failing import check)

- [ ] **Step 1: Write failing parser and validation tests**

```python
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from openpyxl import Workbook, load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import publish_site


class ParseCopyTests(unittest.TestCase):
    def test_parse_structured_copy_uses_explicit_fields(self) -> None:
        copy = """站点：星河 API
链接：https://api.example.com/register?aff=invite123
标签：公益;签到;GPT
备注：注册赠送 10 刀，0.1 倍率
"""

        site = publish_site.parse_site_copy(copy, added_date="2026-07-16")

        self.assertEqual(site.name, "星河 API")
        self.assertEqual(site.url, "https://api.example.com/register?aff=invite123")
        self.assertEqual(site.tags, ("公益", "签到", "GPT"))
        self.assertEqual(site.note, "注册赠送 10 刀，0.1 倍率")
        self.assertEqual(site.added_date, "2026-07-16")

    def test_parse_free_form_copy_derives_only_present_known_tags(self) -> None:
        copy = "星河 API\nhttps://api.example.com/register?ref=abc\n公益 GPT 注册赠送 10 刀"

        site = publish_site.parse_site_copy(copy, added_date="2026-07-16")

        self.assertEqual(site.name, "星河 API")
        self.assertEqual(site.tags, ("公益", "注册赠送", "GPT"))
        self.assertEqual(site.note, "公益 GPT 注册赠送 10 刀")

    def test_parse_rejects_url_without_referral_signal(self) -> None:
        with self.assertRaisesRegex(ValueError, "referral"):
            publish_site.parse_site_copy("站点：星河\nhttps://api.example.com/register", added_date="2026-07-16")

    def test_parse_rejects_missing_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "name"):
            publish_site.parse_site_copy("https://api.example.com/register?aff=abc", added_date="2026-07-16")
```

- [ ] **Step 2: Run the parser tests and verify they fail**

Run: `python -m unittest tests.test_publish_site.ParseCopyTests`

Expected: `ModuleNotFoundError: No module named 'publish_site'`.

- [ ] **Step 3: Extend the test file with workbook, dry-run, and allowlist tests**

```python
class WorkbookTests(unittest.TestCase):
    def workbook(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "sites.xlsx"
        book = Workbook()
        sheet = book.active
        sheet.append(["公益站导航"])
        sheet.append(["序号", "站点", "链接", "标签", "备注", "添加日期"])
        sheet.append([1, "已有站", "https://old.example/register?aff=old", "公益", "已有", "2026-07-01"])
        book.save(path)
        return path

    def test_append_site_adds_next_index_and_date(self) -> None:
        workbook = self.workbook()
        site = publish_site.parse_site_copy(
            "站点：新站\nhttps://new.example/register?aff=new\n标签：公益;GPT\n备注：注册送 1 刀",
            added_date="2026-07-16",
        )

        index = publish_site.append_site(workbook, site)
        row = list(load_workbook(workbook, data_only=True).active.iter_rows(values_only=True))[-1]

        self.assertEqual(index, 2)
        self.assertEqual(row, (2, "新站", site.url, "公益;GPT", "注册送 1 刀", "2026-07-16"))

    def test_append_site_rejects_existing_normalized_domain(self) -> None:
        workbook = self.workbook()
        site = publish_site.parse_site_copy(
            "站点：重复站\nhttps://old.example/register?aff=new\n备注：重复域名",
            added_date="2026-07-16",
        )

        with self.assertRaisesRegex(ValueError, "already exists"):
            publish_site.append_site(workbook, site)

    def test_dry_run_does_not_mutate_workbook(self) -> None:
        workbook = self.workbook()
        before = workbook.read_bytes()
        site = publish_site.parse_site_copy(
            "站点：预览站\nhttps://preview.example/register?aff=preview\n备注：仅预览",
            added_date="2026-07-16",
        )

        result = publish_site.publish(workbook, site, dry_run=True, generate=lambda: None)

        self.assertEqual(result.index, 2)
        self.assertEqual(before, workbook.read_bytes())

    def test_release_paths_are_explicit_and_exclude_reports(self) -> None:
        self.assertIn("ai-api-sites-table.xlsx", publish_site.RELEASE_PATHS)
        self.assertIn("data/sites.json", publish_site.RELEASE_PATHS)
        self.assertNotIn("reports", publish_site.RELEASE_PATHS)
        self.assertNotIn("tools/collect_candidates.py", publish_site.RELEASE_PATHS)
```

- [ ] **Step 4: Run the full new test file and verify it fails**

Run: `python -m unittest tests.test_publish_site`

Expected: failure because `parse_site_copy`, `append_site`, `publish`, and `RELEASE_PATHS` do not exist.

- [ ] **Step 5: Commit the failing test specification**

```powershell
git add -- tests/test_publish_site.py
git commit -m "test: specify AI site publisher behavior"
```

### Task 2: Implement the Deterministic Publisher

**Files:**
- Create: `tools/publish_site.py`
- Test: `tests/test_publish_site.py`

- [ ] **Step 1: Define the public types and constants**

```python
@dataclass(frozen=True)
class ParsedSite:
    name: str
    url: str
    tags: tuple[str, ...]
    note: str
    added_date: str


@dataclass(frozen=True)
class PublishResult:
    site: ParsedSite
    index: int
    dry_run: bool


RELEASE_PATHS = (
    "ai-api-sites-table.xlsx", "index.html", "ai-api-sites-table.html",
    "ai-api-sites-share.html", "README.md", "ai-api-sites-table.md",
    "ai-api-sites-table.csv", "data/sites.json",
    "assets/ai-api-gongyi-nav-cover.png", "robots.txt", "sitemap.xml",
)
```

- [ ] **Step 2: Implement parsing and validation**

Implement `parse_site_copy(copy: str, added_date: str) -> ParsedSite` with these exact rules:

```python
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")
REFERRAL_SIGNALS = ("aff=", "ref=", "invite=", "/invite/")
KNOWN_TAGS = ("公益", "签到", "生图", "稳定", "Claude", "GPT", "DeepSeek",
              "Gemini", "GLM", "MiniMax", "Codex", "注册赠送", "低倍率")
```

Read `站点：`, `链接：`, `标签：`, and `备注：` fields when supplied. Otherwise,
use the first non-empty, non-URL line as the name; use the first extracted URL;
derive tags in `KNOWN_TAGS` order only from literal text matches; and retain the
remaining non-field content as the note. Validate the URL with `urlparse` and
require a referral signal case-insensitively. Raise `ValueError` messages that
contain `name`, `URL`, or `referral` for the matching test failure.

- [ ] **Step 3: Implement workbook mutation and generation boundary**

Implement these functions:

```python
def append_site(workbook_path: Path, site: ParsedSite) -> int: ...
def publish(workbook_path: Path, site: ParsedSite, dry_run: bool, generate: Callable[[], None]) -> PublishResult: ...
def normalized_domain(url: str) -> str: ...
```

`append_site` finds the header row matching the six source headers, reads all
existing URLs, rejects an equal normalized domain with `ValueError("domain
already exists: ...")`, and writes one row with `max(index) + 1`. `publish`
calculates that index without writing in dry-run mode; otherwise it calls
`append_site` and then the injected generator. Import and call
`generate_site.main` only in the CLI `main()` function so unit tests have no
generated-file side effects.

- [ ] **Step 4: Implement the CLI**

Support these commands:

```powershell
python tools\publish_site.py --input C:\path\to\copy.txt --dry-run
python tools\publish_site.py --input C:\path\to\copy.txt
python tools\publish_site.py --release-paths
```

Read `--input` with UTF-8, emit the parsed site and predicted index as
UTF-8 JSON with `ensure_ascii=False`, and exit nonzero with a concise stderr
message on `ValueError`. `--release-paths` prints one allowlisted relative path
per line and does not require `--input`.

- [ ] **Step 5: Run publisher tests and verify they pass**

Run: `python -m unittest tests.test_publish_site`

Expected: all `ParseCopyTests` and `WorkbookTests` pass.

- [ ] **Step 6: Run the repository unit suite**

Run: `python -m unittest discover -s tests`

Expected: existing collector and generator tests plus publisher tests all pass.

- [ ] **Step 7: Commit the implementation**

```powershell
git add -- tools/publish_site.py tests/test_publish_site.py
git commit -m "feat: add AI site publisher"
```

### Task 3: Create and Validate the Repository Skill

**Files:**
- Create: `.agents/skills/publish-ai-site/SKILL.md`
- Create: `.agents/skills/publish-ai-site/agents/openai.yaml`
- Test: `.agents/skills/publish-ai-site/SKILL.md`

- [ ] **Step 1: Record a baseline no-skill workflow**

In a fresh agent context without the new skill, give this prompt:

```text
发布站点：星河 API，注册链接 https://api.example.com/register?aff=abc，公益 GPT，注册送 10 刀。
```

Record whether the agent stages only release files, runs a dry-run first,
checks the test suite, and stops on a remote rejection. Treat any missing
preflight or broad `git add .` as a baseline failure to address in `SKILL.md`.

- [ ] **Step 2: Initialize the skill folder and metadata**

Run the skill creator initializer with `publish-ai-site` as the name and
`.agents/skills` as the path. Generate `agents/openai.yaml` with:

```text
display_name=Publish AI Site
short_description=Publish a validated AI API listing
default_prompt=Publish this AI API site listing from my promotional copy.
```

- [ ] **Step 3: Write the skill workflow**

Give `SKILL.md` frontmatter exactly:

```yaml
---
name: publish-ai-site
description: Use when adding or publishing an AI API public-benefit or relay-site listing from promotional copy in this repository, including validating the referral link, regenerating the static site, committing, and pushing to GitHub.
---
```

Require this sequence in the body:

1. Save the supplied promotional copy to a temporary UTF-8 file outside the
   repository.
2. Run `tools/publish_site.py --input <file> --dry-run`, stop for parse or
   validation failure, and show the parsed name, URL, tags, note, and index.
3. Run the same command without `--dry-run`.
4. Run `python -m unittest discover -s tests` and stop on failure.
5. Inspect `git diff --check` and the changed paths. Obtain paths from
   `python tools/publish_site.py --release-paths`; stage only those paths that
   changed with `git add -- <paths>`.
6. Commit `feat: add <site name> listing` and push with
   `git push origin $(git branch --show-current)`.
7. If the push is rejected, report the local commit hash and stop. Never run
   `git add .`, `git pull`, `git rebase`, `git push --force`, or stage unrelated
   files.

Include the structured copy template from Task 1 and a compact failure table
for incomplete copy, duplicate domains, failed tests, and rejected pushes.

- [ ] **Step 4: Validate the skill structure**

Run: `python C:\Users\30313\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents\skills\publish-ai-site`

Expected: validation succeeds with a valid `name` and `description`.

- [ ] **Step 5: Forward-test the skill in a fresh agent context**

Use the new skill with this prompt:

```text
发布站点：星河 API
链接：https://old.example/register?aff=abc
标签：公益;GPT
备注：注册赠送 10 刀
```

Expected: it uses a dry-run and stops on the duplicate domain before any write,
commit, or push. This validates the guardrail without using a publishable test
listing or accessing GitHub.

- [ ] **Step 6: Commit the skill**

```powershell
git add -- .agents/skills/publish-ai-site
git commit -m "feat: add AI site publishing skill"
```

### Task 4: Final Verification and Handoff

**Files:**
- Verify: `tools/publish_site.py`
- Verify: `tests/test_publish_site.py`
- Verify: `.agents/skills/publish-ai-site/SKILL.md`

- [ ] **Step 1: Verify no generated site data changed during development**

Run: `git diff --name-only HEAD~3..HEAD`

Expected: only the plan's tool, tests, and skill files appear; no site listing
is published during skill implementation.

- [ ] **Step 2: Run the complete test suite**

Run: `python -m unittest discover -s tests`

Expected: all tests pass.

- [ ] **Step 3: Validate the final skill folder again**

Run: `python C:\Users\30313\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents\skills\publish-ai-site`

Expected: validation succeeds.

- [ ] **Step 4: Report the usage contract**

Tell the user that a new Codex session can invoke `$publish-ai-site` or say
`发布站点` followed by a copy block. Include the required fields (name and
referral URL), the automatic commit-and-push behavior, and the fact that a
rejected push leaves a local commit without retrying or rewriting history.
