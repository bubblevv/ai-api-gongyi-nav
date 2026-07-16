# Publish Site URL Deduplication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject duplicate normalized referral URLs while allowing distinct registration URLs on the same domain.

**Architecture:** `tools/publish_site.py` will replace its domain-only comparison with a URL-normalization helper and compare that helper's output against each workbook URL before preview or mutation. The unit suite will define normalization and append behavior, while the repository publishing skill will state the matching stop condition.

**Tech Stack:** Python 3 standard library (`urllib.parse`), openpyxl, unittest, Markdown.

---

### Task 1: Add URL-level duplicate regression coverage

**Files:**
- Modify: `tests/test_publish_site.py:86-96`

- [ ] **Step 1: Replace the existing duplicate-domain test with URL-level tests**

```python
    def test_append_site_rejects_existing_normalized_url(self) -> None:
        workbook = self.workbook()
        site = publish_site.parse_site_copy(
            "站点：重复站\nHTTPS://OLD.EXAMPLE/register/?aff=old\n备注：重复链接",
            added_date="2026-07-16",
        )

        with self.assertRaisesRegex(ValueError, "URL already exists"):
            publish_site.append_site(workbook, site)

    def test_append_site_allows_distinct_referral_url_on_existing_domain(self) -> None:
        workbook = self.workbook()
        site = publish_site.parse_site_copy(
            "站点：同域新链接\nhttps://old.example/register?aff=new\n备注：不同邀请链接",
            added_date="2026-07-16",
        )

        index = publish_site.append_site(workbook, site)

        self.assertEqual(index, 2)
```

- [ ] **Step 2: Run the focused tests to verify the duplicate-link case fails under the current domain-only implementation**

Run:

```powershell
python -m unittest tests.test_publish_site.WorkbookTests.test_append_site_rejects_existing_normalized_url tests.test_publish_site.WorkbookTests.test_append_site_allows_distinct_referral_url_on_existing_domain
```

Expected: the distinct-referral test fails with `domain already exists`; the duplicate-link test currently passes only because the existing domain check is overly broad.

- [ ] **Step 3: Keep the failing regression tests uncommitted until the implementation is green**

The regression test and its implementation form one atomic, passing commit.

### Task 2: Compare normalized complete URLs in the publisher

**Files:**
- Modify: `tools/publish_site.py:12,147-179`
- Test: `tests/test_publish_site.py:86-112`

- [ ] **Step 1: Replace `normalized_domain` with `normalized_url`**

```python
def normalized_url(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    port = parsed.port
    if port is not None and (parsed.scheme.lower(), port) not in {("http", 80), ("https", 443)}:
        host = f"{host}:{port}"
    path = parsed.path.rstrip("/") or "/"
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{parsed.scheme.lower()}://{host}{path}{query}"
```

- [ ] **Step 2: Update `next_index` to compare the helper output and expose the duplicate URL**

```python
def next_index(workbook_path: Path, site: ParsedSite) -> int:
    _, rows = existing_rows(workbook_path)
    url = normalized_url(site.url)
    if any(normalized_url(existing_url) == url for _, existing_url in rows):
        raise ValueError(f"URL already exists: {url}")
    return max((index for index, _ in rows), default=0) + 1
```

- [ ] **Step 3: Run the focused tests to verify both URL behaviors pass**

Run:

```powershell
python -m unittest tests.test_publish_site.WorkbookTests.test_append_site_rejects_existing_normalized_url tests.test_publish_site.WorkbookTests.test_append_site_allows_distinct_referral_url_on_existing_domain
```

Expected: both tests pass.

- [ ] **Step 4: Run the full publisher suite**

Run:

```powershell
python -m unittest tests.test_publish_site
```

Expected: all tests pass with no skipped tests.

- [ ] **Step 5: Commit the implementation**

```powershell
git add -- tests/test_publish_site.py tools/publish_site.py
git commit -m "feat: deduplicate publisher URLs"
```

### Task 3: Synchronize the publish skill wording and safety test

**Files:**
- Modify: `.agents/skills/publish-ai-site/SKILL.md:46,93`
- Modify: `tests/test_publish_site.py:150-154`

- [ ] **Step 1: Update the workflow and stop-condition wording**

Replace both occurrences of `duplicate domain` / `Duplicate normalized domain` with `duplicate normalized URL`. In workflow step 3, retain the instruction to stop before writing, committing, or pushing.

- [ ] **Step 2: Extend the skill safety test with the exact duplicate URL wording**

```python
    def test_skill_stops_for_duplicate_normalized_url(self) -> None:
        skill = (ROOT / ".agents" / "skills" / "publish-ai-site" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Duplicate normalized URL", skill)
```

- [ ] **Step 3: Run the skill safety tests**

Run:

```powershell
python -m unittest tests.test_publish_site.SkillSafetyTests
```

Expected: both safety tests pass.

- [ ] **Step 4: Run the complete test suite and diff validation**

Run:

```powershell
python -m unittest discover -s tests
git diff --check
```

Expected: the full suite passes and `git diff --check` has no output.

- [ ] **Step 5: Commit the skill documentation and its test**

```powershell
git add -- .agents/skills/publish-ai-site/SKILL.md tests/test_publish_site.py
git commit -m "docs: clarify publisher URL deduplication"
```
