---
name: publish-ai-site
description: Use when adding or publishing an AI API public-benefit or relay-site listing from promotional copy in this repository, including validating the referral link, regenerating the static site, committing, and pushing to GitHub.
---

# Publish AI Site

Publish one validated listing from user-supplied copy. The user has authorized
automatic commit and push after validation succeeds; do not request a second
publication confirmation.

## Required Input

Require a site name and an `http` or `https` referral URL with one of `aff=`,
`ref=`, `invite=`, or `/invite/`. A Telegram bot deep link on `t.me` with a
`start=inv_` payload (for example `https://t.me/examplebot?start=inv_123456`)
is also accepted when the promotion is claimed by joining the Telegram group.
Prefer this shape:

```text
站点：星河 API
链接：https://api.example.com/register?aff=invite123
标签：公益;签到;GPT
备注：注册赠送 10 刀，0.1 倍率
```

`标签` and `备注` are optional. The publisher derives only known tags that are
present in free-form copy. Stop before writing when the name, referral URL, or
note cannot be determined.

## Workflow

1. Show `git status --short` so existing changes are visible. Do not stage,
   modify, or clean unrelated files. Require a clean index and unchanged
   release paths before writing:

   ```powershell
   python tools\publish_site.py --preflight
   $releasePaths = @(python tools\publish_site.py --release-paths)
   ```

2. Write the supplied copy to a UTF-8 temporary file outside the repository.
3. Run the preview and inspect its JSON output:

   ```powershell
   python tools\publish_site.py --input $tempFile --dry-run
   ```

   Stop for a parse error or duplicate normalized URL. On success, report the parsed
   name, URL, tags, note, and predicted index, then continue immediately.
4. Publish the source entry and regenerate the site:

   ```powershell
   python tools\publish_site.py --input $tempFile
   python -m unittest discover -s tests
   git diff --check
   ```

   Stop before staging when generation, tests, or diff validation fails.
5. Stage only changed paths from the publisher's allowlist:

   ```powershell
   $changedPaths = @(git diff --name-only)
   $pathsToStage = @($releasePaths | Where-Object { $changedPaths -contains $_ })
   if ($pathsToStage.Count -eq 0) { throw "Publisher changed no release paths." }
   git add -- ai-api-sites-table.xlsx
   $generatedPaths = @($pathsToStage | Where-Object { $_ -ne "ai-api-sites-table.xlsx" })
   if ($generatedPaths.Count -gt 0) { git add -- $generatedPaths }
   $stagedPaths = @(git diff --cached --name-only)
   $unexpectedStagedPaths = @($stagedPaths | Where-Object { $_ -notin $releasePaths })
   if ($unexpectedStagedPaths.Count -gt 0) { throw "Unexpected staged paths: $($unexpectedStagedPaths -join ', ')" }
   git diff --cached --check
   git diff --cached --name-only
   ```

   The only allowable paths are the workbook and generated site files printed
   by `--release-paths`. The workbook is intentionally versioned as the source
   of truth. Never use `git add .` or stage reports, collector code, skills,
   tests, or unrelated working-tree changes.
6. Commit and push the current branch:

   ```powershell
   git commit -m "feat: add <site name> listing"
   $branch = git branch --show-current
   git push origin $branch
   ```

7. Return the name, referral URL, commit hash, branch, and push result. Delete
   the temporary input file after the outcome is known.

## Stop Conditions

| Condition | Required behavior |
| --- | --- |
| Missing or ambiguous copy | Request the missing field; do not write files. |
| Duplicate normalized URL | Stop without writing, committing, or pushing. |
| Generator, tests, or diff check fails | Do not stage, commit, or push. Preserve the diagnostic output. |
| Push is rejected | Report the local commit hash and stop. |

Never run `git pull`, `git rebase`, `git push --force`, or resolve a Git
conflict automatically. A rejected push leaves its local commit intact for
manual resolution.

## Static website maintenance

- The public website is https://bubblevv.github.io/ai-api-gongyi-nav/ and is
  deployed by GitHub Pages from the root of `main`.
- The workbook remains the source of truth. `tools/generate_site.py` renders
  `tools/site_template.html` into the three versioned HTML pages and exports.
  Do not edit the generated HTML directly.
- Sort dated entries by date descending, breaking ties with ID descending.
  Undated historical entries stay last in original ID order; never invent dates.
- Keep all listings and referral URLs in static HTML so they work without
  JavaScript. Search and tag filters enhance that existing content.
- Listing-only releases use the allowlist above. A user-requested website
  redesign may also commit its explicitly changed generator, template, tests,
  and maintenance documentation after validation; leave unrelated files alone.
- After pushing, check GitHub Pages build status and fetch the public HTML to
  verify the deployed content. Do not claim search-engine indexing or rankings.
- See `docs/site-publishing.md` for the maintenance and deployment checklist.
