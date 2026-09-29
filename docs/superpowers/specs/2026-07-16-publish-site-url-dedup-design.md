# Publish Site URL Deduplication Design

## Goal

Permit multiple referral registrations on one domain while preventing the same
registration link from being published more than once.

## Rule

The publisher compares normalized complete URLs, rather than normalized
domains. URL normalization:

- lowercases the scheme and host;
- removes the default HTTP/HTTPS port; and
- removes a trailing slash from a non-root path, and treats an empty path and
  `/` as the same path.

The path and query string remain significant. Therefore, links on the same
domain with different registration paths or different referral parameters are
valid distinct listings.

## Behavior

Before both dry-run preview and workbook mutation, the publisher reads existing
workbook URLs and rejects a candidate whose normalized URL matches an existing
one. The error identifies the duplicate URL. It makes no workbook or generated
file changes on rejection.

The publication skill's preview and stop-condition text use the same
"duplicate normalized URL" wording, so the documented operational procedure
matches the enforced validation.

## Tests

Tests cover these outcomes:

- the same URL, including host case and trailing-slash variants, is rejected;
- a different referral URL on the same domain is accepted; and
- a duplicate rejection leaves the workbook unchanged.

## Non-goals

This does not infer that different query parameters represent equivalent
campaigns, de-duplicate across different domains, or alter existing listings.
