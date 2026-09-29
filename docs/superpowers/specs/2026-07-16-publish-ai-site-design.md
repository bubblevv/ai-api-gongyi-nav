# Publish AI Site Skill Design

## Goal

Provide a repository-specific Codex skill that publishes a new AI API site from
user-supplied promotional copy. A successful run updates the source workbook,
regenerates the static site, validates the change, commits only the release
files, and pushes the current branch to `origin`.

## Location and Trigger

Store the skill in `.agents/skills/publish-ai-site/` so Codex discovers it for
this repository. The skill is invoked with `$publish-ai-site` or a request such
as "发布站点" followed by the promotional copy.

## Components

### Skill instructions

`SKILL.md` defines the operator workflow, required preflight checks, accepted
copy fields, and stop conditions. It directs Codex to use the publishing tool
instead of editing generated site files directly.

### Publishing tool

`tools/publish_site.py` accepts one local UTF-8 text input. It extracts a
candidate name, referral URL, tags, and note; validates the candidate; appends
one row to `ai-api-sites-table.xlsx`; and runs `tools/generate_site.py`.

The tool exposes a dry-run mode for tests and diagnostics. The normal mode is
used by the skill only after it has shown the parsed record in its response.

## Data Contract

Input is free-form Chinese promotional copy. It must contain:

- A site name, either supplied as `站点：...` or inferred from a non-empty
  first line.
- One valid `http` or `https` URL.
- A referral signal in the URL: `aff=`, `ref=`, `invite=`, or `/invite/`.

Optional fields are `标签：` and `备注：`. When tags are absent, the tool derives
only known tags from the copy; it does not invent claims. The added date is the
local date in `YYYY-MM-DD` form. The row index is the current maximum index
plus one.

## Validation and Safety

The tool stops before writing when the name or referral URL is missing, the URL
is malformed, or its normalized domain already exists in the workbook. It also
stops if the generator fails.

The skill runs the full unit suite before committing. It stages an explicit
allowlist only:

- `ai-api-sites-table.xlsx`
- `index.html`
- `ai-api-sites-table.html`
- `ai-api-sites-share.html`
- `README.md`
- `ai-api-sites-table.md`
- `ai-api-sites-table.csv`
- `data/sites.json`
- `assets/ai-api-gongyi-nav-cover.png`
- `robots.txt`
- `sitemap.xml`

It never stages reports, collector files, or unrelated working-tree changes.
The workflow commits with `feat: add <site name> listing` and pushes with
`git push origin <current branch>` without a second publication confirmation,
as requested.

If the remote rejects the push, the skill reports the local commit and stops.
It does not automatically pull, rebase, force-push, or resolve conflicts.

## Workflow

1. Receive the site copy and write it to a temporary UTF-8 file.
2. Run the publisher in dry-run mode and show the parsed record.
3. Run the publisher to update the workbook and generated files.
4. Run `python -m unittest discover -s tests`.
5. Inspect the allowlisted diff and ensure a new row is present.
6. Stage only the allowlist paths that changed, commit, and push the current
   branch.
7. Return the site name, URL, commit hash, branch, and push result.

## Failure Handling

| Condition | Behavior |
| --- | --- |
| Ambiguous or incomplete copy | Stop and request the missing field. |
| Existing domain | Stop without changing files and report the existing entry. |
| Validation or generator failure | Stop before commit and preserve the diagnostic output. |
| Test failure | Do not stage, commit, or push. |
| Push rejection | Leave the created local commit intact and report how to continue. |

## Tests

Unit tests cover structured and free-form parsing, tag derivation, duplicate
domain rejection, dry-run non-mutation, workbook append behavior, and the
explicit staging allowlist. Existing generator tests remain part of the full
suite.

## Non-goals

This skill does not scrape QQ, automatically publish unreviewed collector
candidates, validate third-party service quality, access logged-in QQ data, or
resolve Git conflicts automatically.
