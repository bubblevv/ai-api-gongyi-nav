# IMES Database Debugging Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the customer-bound `zydmes-db-debugging` personal skill with a reusable `imes-db-debugging` skill that preserves common IMES database knowledge without hardcoding a customer database or connection.

**Architecture:** Keep one concise skill entry point, one environment-aware workflow reference, one cross-customer IMES pattern reference, and matching UI metadata. Rename the skill directory atomically, then remove customer-specific assumptions while retaining SQL Server, BDJB, PDA, reporting, material issue, batch, transaction, and result-set guidance.

**Tech Stack:** Markdown, YAML, PowerShell, Python `quick_validate.py`, Codex skill metadata.

---

### Task 1: Capture the Existing Hardcoding Failure

**Files:**
- Read: `C:\Users\30313\.codex\skills\zydmes-db-debugging\SKILL.md`
- Read: `C:\Users\30313\.codex\skills\zydmes-db-debugging\references\workflow.md`
- Read: `C:\Users\30313\.codex\skills\zydmes-db-debugging\references\patterns.md`

- [ ] **Step 1: Run a baseline scenario against the existing skill**

Use a fresh agent with this exact task and do not reveal the intended rewrite:

```text
Use $zydmes-db-debugging at C:\Users\30313\.codex\skills\zydmes-db-debugging to plan a safe investigation for a stored-procedure error in database SGMYMES. The current SQL file contains USE [SGMYMES]. Do not connect to a database or edit files. State which database environment, output directory, and verification workflow you would use.
```

- [ ] **Step 2: Verify the baseline fails the portability requirement**

Expected failure evidence: the response selects or recommends `ZYDMES正式`, `USE [ZYDMES]`, `diagnostics/ZYDMES_*`, or another ZYDMES-specific path despite the prompt specifying `SGMYMES`.

- [ ] **Step 3: Record the exact hardcoded assumptions found**

Record only the raw response and these categories in the execution notes: database name, connection environment, local credential/config path, diagnostic directory prefix, customer-specific incidents.

### Task 2: Rename and Generalize the Skill

**Files:**
- Rename: `C:\Users\30313\.codex\skills\zydmes-db-debugging` to `C:\Users\30313\.codex\skills\imes-db-debugging`
- Modify: `C:\Users\30313\.codex\skills\imes-db-debugging\SKILL.md`
- Modify: `C:\Users\30313\.codex\skills\imes-db-debugging\references\workflow.md`
- Modify: `C:\Users\30313\.codex\skills\imes-db-debugging\references\patterns.md`
- Modify: `C:\Users\30313\.codex\skills\imes-db-debugging\agents\openai.yaml`

- [ ] **Step 1: Rename the directory after verifying the source and destination**

Run:

```powershell
$source = 'C:\Users\30313\.codex\skills\zydmes-db-debugging'
$target = 'C:\Users\30313\.codex\skills\imes-db-debugging'
if (-not (Test-Path -LiteralPath $source)) { throw "Missing source: $source" }
if (Test-Path -LiteralPath $target) { throw "Target already exists: $target" }
Move-Item -LiteralPath $source -Destination $target
```

Expected: the old path is absent and the new path contains `SKILL.md`, `agents/`, and `references/`.

- [ ] **Step 2: Replace `SKILL.md` with the generic entry point**

The frontmatter must be:

```yaml
---
name: imes-db-debugging
description: Use when diagnosing or changing IMES SQL Server business logic, stored procedures, BDJB audit scripts, PDA save/get interfaces, reporting, material issue, batch, transaction, result-set, or production database errors across customer environments.
---
```

The body must require runtime environment discovery in this order: explicit user target, current SQL `USE`/qualified names, project rules/configuration, configured database tools. It must forbid guessing a database or connection and retain rollback-safe verification, stable result contracts, minimal compatible changes, and self-improvement of reusable patterns.

- [ ] **Step 3: Rewrite `references/workflow.md` around environment discovery**

Replace fixed paths and `ZYDMES正式` with a generic process:

```text
1. Identify database and environment from the request or current artifact.
2. Inspect project rules and configured database-tool environments.
3. Resolve credentials only through existing secure configuration or environment variables.
4. If multiple targets match, ask before connecting or changing data.
5. Use the discovered database value for sqlcmd -d and generated USE statements.
6. Name diagnostics folders diagnostics/<database>_<object>_<yyyymmdd>/ only when the repository uses diagnostics/.
```

Keep the investigation, minimal-change, parse, deploy-confirmation, focused-query, and rollback-wrapped execution guidance. Do not include a concrete customer database, environment name, username, password, server, or user-specific credential path.

- [ ] **Step 4: Rewrite `references/patterns.md` as cross-customer IMES knowledge**

Keep reusable sections for:

```text
BDJB execution and result-set hygiene
PDA save/get interfaces
reportable quantity reasoning
material issue validation
batch allocation and update chains
transaction/savepoint behavior
MES-to-ERP synchronization invariants
```

Remove dated incident headings, concrete `BDJB_ID` values, customer-specific database names, and conclusions that apply only to one customer's configuration. Label object names such as `PRD_MES_PDA_*`, `MESCZBG*`, `MESSCPKL*`, `SCDD*`, and `SCLLD*` as common examples that must be confirmed against the target customer's schema.

- [ ] **Step 5: Update `agents/openai.yaml`**

Use exactly:

```yaml
interface:
  display_name: "IMES 数据库排错"
  short_description: "跨客户定位 IMES 业务 SQL、BDJB、PDA 和存储过程问题"
  default_prompt: "使用 $imes-db-debugging，帮我安全定位并修复这个 IMES 数据库业务 SQL 或存储过程问题。"
```

### Task 3: Validate Structure and Remove Customer Binding

**Files:**
- Validate: `C:\Users\30313\.codex\skills\imes-db-debugging\SKILL.md`
- Validate: `C:\Users\30313\.codex\skills\imes-db-debugging\references\workflow.md`
- Validate: `C:\Users\30313\.codex\skills\imes-db-debugging\references\patterns.md`
- Validate: `C:\Users\30313\.codex\skills\imes-db-debugging\agents\openai.yaml`

- [ ] **Step 1: Run the official skill validator**

Run:

```powershell
python C:\Users\30313\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\30313\.codex\skills\imes-db-debugging
```

Expected: validation succeeds with exit code `0`.

- [ ] **Step 2: Scan for forbidden customer-specific content**

Run:

```powershell
rg -n -i "ZYDMES|SGMYMES|ZYDMES正式|CMCSYUN|EPMS_Haha|BDJB_ID\s*=\s*\d+|C:\\Users\\30313\\.codex\\mcp" C:\Users\30313\.codex\skills\imes-db-debugging
```

Expected: no matches.

- [ ] **Step 3: Scan for required portable behavior and IMES knowledge**

Run:

```powershell
rg -n -i "runtime|运行时|USE|project|项目|configured|配置|BDJB|PDA|报工|领料|批号|savepoint|回滚|result set|结果集" C:\Users\30313\.codex\skills\imes-db-debugging
```

Expected: matches cover environment discovery, safe verification, and every retained IMES business area.

- [ ] **Step 4: Verify the old skill path is gone**

Run:

```powershell
Test-Path -LiteralPath C:\Users\30313\.codex\skills\zydmes-db-debugging
```

Expected: `False`.

### Task 4: Forward-Test Portability

**Files:**
- Test: `C:\Users\30313\.codex\skills\imes-db-debugging`

- [ ] **Step 1: Re-run the SGMYMES scenario with the new skill**

```text
Use $imes-db-debugging at C:\Users\30313\.codex\skills\imes-db-debugging to plan a safe investigation for a stored-procedure error in database SGMYMES. The current SQL file contains USE [SGMYMES]. Do not connect to a database or edit files. State which database environment, output directory, and verification workflow you would use.
```

Expected: use `SGMYMES` from the artifact, discover the matching configured environment instead of inventing one, and derive any diagnostic folder from `SGMYMES`.

- [ ] **Step 2: Run a second-customer scenario**

```text
Use $imes-db-debugging at C:\Users\30313\.codex\skills\imes-db-debugging to plan a safe investigation for an INSERT EXEC result-set mismatch. The only confirmed target is database CLIENT_B_IMES. Do not connect or edit files. Explain how you will discover the connection and verify the procedure safely.
```

Expected: keep `CLIENT_B_IMES`, require discovery of an existing configured connection, retain BDJB/PDA result-set and rollback guidance, and avoid every forbidden customer-specific value.

- [ ] **Step 3: Review both outputs for portability**

Fail the test if either output invents a fixed environment, changes the supplied database, embeds credentials, or treats example IMES object names as guaranteed schema.

- [ ] **Step 4: Report completion**

Report the renamed path, removed customer bindings, retained IMES business patterns, validator result, forbidden-pattern scan result, and forward-test outcomes. State explicitly that no database was contacted.
