# Tool Surface Audit — `portfoliosMCP_v2`

**Date:** 2026-08-24  
**Scope:** Registered MCP tools only (`TOOL_NAMES` in `tool_registry.py` / `TOOL_IMPLEMENTATIONS` in `server.py`).  
**Constraint:** Tool count is a design decision about the model's interface, not a function of the API surface.

## Decisions (follow-up)

1. **OKRs are out.** Not a demo job. `list_objectives`, `get_key_results_for_objective`, and `list_all_objectives_with_key_results` are unregistered and `tools/okrs.py` is removed. `portfolios-apis/okrs-api-main` stays as API reference only.
2. **Keep a connection tool.** Rename `oauth_ping` → `test_connection`. It stays on the model surface. It must diagnose, not just ping.
3. **OAuth errors with "fresh tokens"** are usually one of: JWT pasted into `PLANVIEW_CLIENT_SECRET`, missing `/polaris` or uppercase host, empty/wrong `PLANVIEW_TENANT_ID` (token succeeds, ping 401s), or a stale `Authorization` header on the pooled REST client after a later token fetch.
4. **Parent structure codes come from the Planview UI**, not this MCP. Create needs the work-hierarchy PPL-1 folder. Local REST/SOAP cannot list `$Plan` parents. **`$Strategy` is out of scope.**

**Headline:** 24 registered tools → **21 now** (OKRs pulled, ping renamed) → **5 proposed tools** for the later consolidation (`test_connection`, `manage_project`, `inspect_work`, `manage_tasks`, `manage_financial_plan`).

Unregistered REST helpers in `tools/resources.py` (`list_resources`, `get_resource`, `allocate_resource`) are **out of scope** for the model-facing redesign. They never appear in `list_tools`.

---

## Counts

| | Count |
|---|---|
| Current registered tools | **21** (was 24; OKRs removed) |
| Classified ENDPOINT | 16 remaining wrappers + `test_connection` |
| Classified JOB | 4 (WBS, field catalog, financial discover, financial copy) |
| Proposed model-facing tools | **5** |
| Proposed in-process modules (model never sees these) | 7 |
| First-class connection tool | `test_connection` (replaces `oauth_ping`) |
| Pulled from the model surface | OKR tools (`list_objectives`, `get_key_results_for_objective`, `list_all_objectives_with_key_results`) |

---

## Step 1 — Inventory

Shared infrastructure used by many tools is summarized after the per-tool list.

### 1. `oauth_ping` — REST

**Description:** Auth health check. Calls secured ping to verify credentials.

**Input schema:** `{}` (no properties)

**Endpoint:** `GET {PLANVIEW_API_URL}/public-api/v1/oauth/ping`

**Shared logic:** REST auth (`get_client` → OAuth bearer + `X-Tenant-Id`), REST retry (`make_request`), HTTP error shaping (`PlanviewAuthError` / etc.). Response-type branching (JSON vs `text/plain` "pong") is local.

---

### 2. `get_project` — REST

**Description:** Single project read by ID. Routing hint: use Anvi Prod for list/search.

**Input schema:** `project_id` (required string), `attributes` (optional array | string | null)

**Endpoint:** `GET /public-api/v1/projects/{project_id}`

**Shared logic:** REST auth, retry, error shaping, `_format_attributes` (duplicated with `work.py`), per-tool try/except logging boilerplate.

---

### 3. `get_project_attributes` — REST

**Description:** Raw list of available project attributes. Routing hint: use Anvi Prod `searchAttributes` for NL search.

**Input schema:** `{}`

**Endpoint:** `GET /public-api/v1/projects/attributes/available`

**Shared logic:** REST auth, retry, error shaping, logging boilerplate. Live catalog is ~779 attributes; the demo field list is a separate static module (`src/field_reference.py`), not this endpoint.

---

### 4. `create_project` — REST (+ optional SOAP)

**Description:** Create a project. Auto-defaults `scheduleStart`/`scheduleFinish` if omitted. Optional `create_default_tasks` seeds five sample tasks.

**Input schema:** `data` (required object — CreateProjectDtoPublic), `attributes` (optional), `create_default_tasks` (boolean, default false)

**Endpoints:**
- `POST /public-api/v1/projects`
- If `create_default_tasks=true`: SOAP `ITaskService3.Create` via `batch_create_tasks` (see tasks)

**Shared logic:** REST auth/retry/errors; `extract_project_info` for nested `data[]`; date defaulting; **two-pass** into SOAP when seeding tasks. Task-seed failure is swallowed — project still returns success.

---

### 5. `update_project` — REST

**Description:** Partial PATCH of project fields. Isolates lifecycle-blocked fields on 400.

**Input schema:** `project_id` (required), `updates` (required object), `attributes` (optional)

**Endpoint:** `PATCH /public-api/v1/projects/{project_id}`  
On multi-field 400: **N additional PATCHes**, one field at a time, to name the blocked field.

**Shared logic:** REST auth/retry/errors; `_format_attributes`; **field-isolation write pattern duplicated with `update_work`**. Isolation is mutating — succeeded fields stay written even if the tool then raises.

---

### 6. `delete_project` — REST

**Description:** Destructive delete of a project and child data.

**Input schema:** `project_id` (required)

**Endpoint:** `DELETE /public-api/v1/projects/{project_id}`

**Shared logic:** REST auth/retry/errors. Empty/204 body normalized to `{success, deleted_project_id}`.

---

### 7. `list_field_reference` — local (no API)

**Description:** Browse curated writable project fields by category (~120 demo-relevant fields from 427 writable).

**Input schema:** `category` (optional string | null)

**Endpoint:** none. Reads `src/field_reference.py` (`FIELD_CATEGORIES`).

**Shared logic:** none with HTTP. This is the discovery path demos actually use; `get_project_attributes` is the live dump.

---

### 8. `get_project_wbs` — REST (composed)

**Description:** Nested WBS tree with schedule data, stats, optional milestone pruning and max depth.

**Input schema:** `project_id` (required), `include_milestones` (bool, default true), `max_depth` (optional int)

**Endpoint:** `GET /public-api/v1/work?filter=project.Id .eq {project_id}` via `list_work` (not a dedicated WBS API). Tree assembly is in-process.

**Shared logic:** all of `list_work` (auth, retry, filter-variant fallbacks, field trimming).

---

### 9. `get_work` — REST

**Description:** Read any single work hierarchy node by ID.

**Input schema:** `work_id` (required), `attributes` (optional)

**Endpoint:** `GET /public-api/v1/work/{work_id}`

**Shared logic:** REST auth/retry/errors, `_format_attributes`, logging boilerplate.

---

### 10. `list_work` — REST

**Description:** Query work items with a filter string (e.g. `project.Id .eq 1906`). Optional per-item field trim.

**Input schema:** `filter` (required), `attributes` (optional), `fields` (optional string array)

**Endpoint:** `GET /public-api/v1/work?filter=...`  
On 400: retries filter variants (`project.Id` → `project.structureCode` → `structureCode`, quoted digits) then a percent-encoded query string.

**Shared logic:** REST auth/retry/errors, `_format_attributes`. **No pagination** — one shot, whatever the instance returns. Filter-retry is unique to this tool.

---

### 11. `update_work` — REST

**Description:** PATCH a work item (phases/tasks). Some instances return 405.

**Input schema:** `work_id` (required), `updates` (required object), `attributes` (optional)

**Endpoint:** `PATCH /public-api/v1/work/{work_id}`  
On 405: maps to a validation error telling the model to use `update_project` for PPL items. On multi-field 400: same mutating field-isolation as `update_project`.

**Shared logic:** REST auth/retry/errors; field-isolation pattern shared with `update_project`.

---

### 12. `get_work_attributes` — REST

**Description:** Raw work attribute catalog.

**Input schema:** `{}`

**Endpoint:** `GET /public-api/v1/work/attributes/available`

**Shared logic:** identical shape to `get_project_attributes`.

---

### 13. `create_task` — SOAP

**Description:** Create one task (planning entity below PPL) via TaskService.

**Input schema:** `task_data` (required object — TaskDto2), `options` (optional WorkOptionsDto; accepted, **not currently sent**)

**Endpoint:** SOAP `TaskService` / `BasicHttpBinding_ITaskService3` → `Create`  
WSDL: `{host}/planview/services/TaskService.svc?wsdl` (host is `PLANVIEW_API_URL` with `/polaris` stripped)

**Shared logic:** SOAP OAuth session, OpenSuite XML→JSON (`_handle_soap_result`), `filter_and_sort_fields` (PascalCase + alpha sort), key URI validation conceptually (not enforced on create). Serialization fallbacks (raw dict → TaskDto2 → ArrayOfTaskDto2) are **local and duplicated** with batch create. **Does not use `make_soap_request`**, so the SOAP retry decorator does not wrap this write.

---

### 14. `batch_create_tasks` — SOAP

**Description:** Create many tasks in one SOAP Create. Returns per-item success/failure.

**Input schema:** `tasks` (required array of objects), `options` (optional; validated, **not sent**)

**Endpoint:** same `ITaskService3.Create` with `ArrayOfTaskDto2`

**Shared logic:** SOAP session, `_parse_opensuite_result` (not `_handle_soap_result` — so partial failure is returned instead of raised), `filter_and_sort_fields`, SourceIndex mapping. Chunking is **not** used (one payload). Retry decorator not applied (direct `asyncio.to_thread`).

---

### 15. `read_task` — SOAP

**Description:** Read a task by `key://`, `search://`, or `ekey://`.

**Input schema:** `task_key` (required)

**Endpoint:** `ITaskService3.Read` (`keys=[task_key]`)

**Shared logic:** SOAP session, `make_soap_request` (**has retry**), `_handle_soap_result` (raises on any failure), `validate_task_key`.

---

### 16. `delete_task` — SOAP

**Description:** Delete a task (cascades to children).

**Input schema:** `task_key` (required)

**Endpoint:** `ITaskService3.Delete` (`keys=[task_key]`)

**Shared logic:** same as `read_task` (`make_soap_request` + `_handle_soap_result`). README notes batch delete parsing is flaky; single delete uses the raising path.

---

### 17. `batch_delete_tasks` — SOAP

**Description:** Bulk delete with per-key results. Chunk size 50.

**Input schema:** `task_keys` (required string array)

**Endpoint:** `ITaskService3.Delete` per chunk of 50 keys

**Shared logic:** SOAP session, `_parse_opensuite_result` (partial allowed), `validate_task_key`. Direct `asyncio.to_thread` — no `make_soap_request` retry. Known parsing reliability issues (README).

---

### 18. `read_financial_plan` — SOAP

**Description:** Read plan structure (accounts, periods, lines). Payload can be huge; `include_entries`/`summary`/`fields` trim it.

**Input schema:** `entity_key`, `version_key` (required); `include_entries` (default false), `summary` (default false), `fields` (optional)

**Endpoint:** SOAP `FinancialPlanService` / `BasicHttpBinding_IFinancialPlanService2` → `Read`  
WSDL: `{host}/planview/services/FinancialPlanService.svc?wsdl`

**Shared logic:** per-service SOAP client cache (`get_soap_client_for_service`), DTO/ArrayOf wrapping, `_handle_soap_result`, `_filter_financial_plan_response`, not-found guidance. Direct `asyncio.to_thread` — no SOAP retry decorator.

---

### 19. `upsert_financial_plan` — SOAP

**Description:** Create or update plan lines. SOAP often echoes empty `Lines` even on success.

**Input schema:** `plan_data` (required object — Key **or** EntityKey+VersionKey, plus `Lines`)

**Endpoint:** `IFinancialPlanService2.Upsert`

**Shared logic:** same SOAP client/DTO/XML path as read; PascalCase normalization (local, not `filter_and_sort_fields`); "No editable lines" / "Account not found" guidance pointing at discover/read. Direct `asyncio.to_thread`.

---

### 20. `discover_financial_plan_info` — SOAP + local config (composed)

**Description:** Discover accounts/periods with fallback: target Read → reference Read → `financial_plan_config`.

**Input schema:** `entity_key` (required), `version_key` (default `key://14/1`), `reference_entity_key`, `skip_target_read`, `include_entries`, `summary`, `fields`

**Endpoints:** `IFinancialPlanService2.Read` (0–2 times). May hit **no API** (config fast path).

**Shared logic:** `read_financial_plan`, `_filter_financial_plan_response`, `financial_plan_config.list_available_accounts/periods`.

---

### 21. `load_financial_plan_from_reference` — REST + SOAP (composed)

**Description:** Copy account structure and values from a reference project onto a target. Dry-run unless `confirm=true`.

**Input schema:** `target_project_id`, `reference_project_id` (required); `version_key` (default `key://14/1`), `scale_factor` (default 1.0), `confirm` (default false)

**Endpoints (multi-pass):**
1. `GET /public-api/v1/projects/{target}` (schedule dates)
2. `GET /public-api/v1/projects/{reference}` (schedule dates)
3. SOAP `Read` reference (entries on)
4. SOAP `Read` target periods (or `discover_financial_plan_info` fallback)
5. If `confirm=true`: SOAP `Upsert` onto target

**Shared logic:** `get_project`, `read_financial_plan`, `discover_financial_plan_info`, `upsert_financial_plan`, period remapping + scale.

---

### 22. `list_objectives` — REST (OKR host)

**Description:** Paginated list of OKR objectives.

**Input schema:** `ids` (optional comma-separated), `limit` (1–500, default 10), `offset` (default 0)

**Endpoint:** `GET {OKR_BASE}/v1/objectives`  
Default host: `https://api-us.okrs.planview.com/api/rest` — **not** the Portfolios API.

**Shared logic:** **separate OKR OAuth/static bearer** (`_get_okr_client` / `get_okr_oauth_token`), then `make_request` retry + HTTP error shaping. Only tool that exposes offset/limit to the model.

---

### 23. `get_key_results_for_objective` — REST (OKR host)

**Description:** Key results for one objective.

**Input schema:** `objective_id` (required integer)

**Endpoint:** `GET {OKR_BASE}/v1/objectives/{objective_id}/key-results`

**Shared logic:** OKR auth + `make_request`.

---

### 24. `list_all_objectives_with_key_results` — REST (OKR host, composed)

**Description:** Walk all objective pages, then optionally N+1 fetch key results per objective.

**Input schema:** `limit` (page size, default 500), `include_key_results` (default true)

**Endpoints:** `GET /v1/objectives` (paginated) + `GET /v1/objectives/{id}/key-results` once per objective.

**Shared logic:** `list_objectives` + `get_key_results_for_objective`. Per-objective KR failures become empty arrays (partial success). This is the only real pagination walker in the server.

---

### Shared logic map (as implemented today)

| Concern | Where it lives | Who uses it | Duplication / gap |
|---|---|---|---|
| Portfolios OAuth token cache + 401 refresh | `oauth.py`, `client.py` | All Portfolios REST | OKR has a **second** token manager |
| REST connection pool + retry (429/502/503/504) | `client.make_request` | All REST including OKR HTTP | OKR builds a **new httpx client per call** (no pool) |
| SOAP session + WSDL cache | `soap_client.py` (`get_soap_client`, `get_soap_client_for_service`) | Tasks + financial plans | Two client factories (TaskService vs per-path) |
| SOAP retry decorator | `soap_client.make_soap_request` | **Only** `read_task`, `delete_task` | Writes (create/batch/upsert/read plan) bypass it |
| OpenSuite XML → dict | `_parse_opensuite_result`, `_convert_zeep_*`, `_handle_soap_result` | All SOAP | `_handle` raises on any failure; batch tools parse raw to allow partials |
| PascalCase + alpha-sort | `utils/soap_helpers.filter_and_sort_fields` | Task create/batch | Financial upsert reimplements PascalCase locally |
| HTTP → `Planview*` errors | `client.make_request`, `exceptions.py` | REST | SOAP faults mapped separately in `make_soap_request`; writes that skip it raise raw zeep/httpx or wrap ad hoc |
| Attribute query param | `_format_attributes` | projects + work | **Copy-pasted** in two files |
| Field-isolation PATCH | `update_project`, `update_work` | those two | Identical mutating retry |
| Pagination | `okrs.list_all_objectives_with_key_results` | OKRs only | `list_work` has **none**; SOAP batch delete uses chunking, not pagination |
| Instance account/period keys | `financial_plan_config.py` | discover fallback | Hardcoded demo keys, not a tool |
| Curated writable fields | `src/field_reference.py` | `list_field_reference`, docstring appendices | Parallel to live attribute endpoints |
| Per-tool logging/timing | `@log_performance` + copy-pasted try/except | every tool | Boilerplate, not a module |
| In-memory TTL cache | `cache.py` | documented; `clear_cache` is **not registered** | Dead surface |

---

## Step 2 — Classify

A **JOB** is something a person would say out loud. An **ENDPOINT** is a 1:1 mirror of a REST or SOAP operation. Composition, fallbacks, and tree-building count as JOB even if they call one endpoint underneath.

| Tool | Class | Why |
|---|---|---|
| `oauth_ping` | **ENDPOINT** | Ping. Nothing a demo audience asks for. |
| `get_project` | **ENDPOINT** | `GET /projects/{id}`. |
| `get_project_attributes` | **ENDPOINT** | `GET .../attributes/available`. |
| `create_project` | **ENDPOINT** | `POST /projects`. Date defaults and optional task seed are decorations, not a different job shape. |
| `update_project` | **ENDPOINT** | `PATCH /projects/{id}`. |
| `delete_project` | **ENDPOINT** | `DELETE /projects/{id}`. |
| `list_field_reference` | **JOB** | "What can I set on this project?" — local catalog, not an API. |
| `get_project_wbs` | **JOB** | "Show me the WBS." Composes `list_work` + tree. |
| `get_work` | **ENDPOINT** | `GET /work/{id}`. |
| `list_work` | **ENDPOINT** | `GET /work?filter=`. Filter language is API-shaped, not job-shaped. |
| `update_work` | **ENDPOINT** | `PATCH /work/{id}`. |
| `get_work_attributes` | **ENDPOINT** | Live work attribute dump. |
| `create_task` | **ENDPOINT** | SOAP `Create` of one TaskDto2. |
| `batch_create_tasks` | **ENDPOINT** | Same `Create`, array. Bulk is an API batch, not a new job. |
| `read_task` | **ENDPOINT** | SOAP `Read`. |
| `delete_task` | **ENDPOINT** | SOAP `Delete`. |
| `batch_delete_tasks` | **ENDPOINT** | Same `Delete`, chunked. |
| `read_financial_plan` | **ENDPOINT** | SOAP `Read`. |
| `upsert_financial_plan` | **ENDPOINT** | SOAP `Upsert`. |
| `discover_financial_plan_info` | **JOB** | "What accounts/periods can I use?" with fallbacks. |
| `load_financial_plan_from_reference` | **JOB** | "Copy financials from that project onto this one." |
| `list_objectives` | **ENDPOINT** | `GET /v1/objectives`. |
| `get_key_results_for_objective` | **ENDPOINT** | `GET .../key-results`. |
| `list_all_objectives_with_key_results` | **JOB** | "Show me OKRs" — paginate + attach KRs. |

**Score: 19 ENDPOINT / 5 JOB.** The model is currently talking to the API, not to the user.

---

## Step 3 — Cluster

Endpoint wrappers grouped into the **smallest set of spoken jobs** that cover their combined functionality. Existing JOB tools are absorbed into the same clusters (not preserved as extra tools).

### Cluster A — `manage_project`

**Jobs it serves:** "Create a project under this parent." "Update this project's status / RAG / dates." "What's on this project after I wrote it?" "Delete that demo project." "What fields can I write?"

**Absorbs:** `get_project`, `create_project`, `update_project`, `delete_project`, `list_field_reference`, `get_project_attributes`

**Shape:** `action`: `create` | `get` | `update` | `delete` | `fields`. `fields` returns the curated catalog (not the 779-row live dump). Live `get_project_attributes` becomes an internal helper if a field ID is missing from the catalog.

**Not absorbed:** work-node PATCH and WBS — different URL, different lifecycle rules, different spoken job.

---

### Cluster B — `inspect_work`

**Jobs it serves:** "Show me the WBS for this project." "Get this phase/node." "Set ExecType on this work item."

**Absorbs:** `get_project_wbs`, `list_work`, `get_work`, `update_work`, `get_work_attributes`

**Shape:** `action`: `wbs` | `get` | `list` | `update`. Default `wbs` — that is the demo read. `list` with raw filter stays available internally; the model should pass `project_id` and get a tree, not invent `project.Id .eq`.

**Drop from model surface:** `get_work_attributes` as its own tool (same rationale as project attributes).

---

### Cluster C — `manage_tasks`

**Jobs it serves:** "Add these tasks under the project." "What is this task?" "Remove those tasks."

**Absorbs:** `create_task`, `batch_create_tasks`, `read_task`, `delete_task`, `batch_delete_tasks`

**Shape:** `action`: `create` | `read` | `delete`. `create` always accepts a list (length 1 is fine). `delete` always accepts a list. No separate batch tools — batch is an implementation detail of SOAP Create/Delete.

**Not exposed:** SOAP `Update` (already unsupported). Model is told: patch schedule via delete+recreate or the UI.

---

### Cluster D — `manage_financial_plan`

**Jobs it serves:** "Show me financials for this project." "Set these budget lines." "Copy financials from the reference project."

**Absorbs:** `read_financial_plan`, `upsert_financial_plan`, `discover_financial_plan_info`, `load_financial_plan_from_reference`

**Shape:** `action`: `read` | `discover` | `upsert` | `copy`. `copy` keeps dry-run (`confirm=false`) as the default. `discover` stays an action, not a tool — the model should not have to know the fallback chain.

---

### Cluster E — `test_connection`

**Jobs it serves:** "Is this MCP actually connected to Planview?" "Why am I getting OAuth errors with a fresh token?"

**Absorbs:** `oauth_ping`

**Shape:** no inputs. Always returns `{ok, connected, checks[], error?}` so a 401 is a diagnosis, not a dead tool error. Checks: config (URL/`/polaris`, JWT-as-secret detection) → token (encoding fallbacks) → secured ping with that same token.

**Pulled, not clustered:** `list_objectives`, `get_key_results_for_objective`, `list_all_objectives_with_key_results`. OKRs are not a demo job.

---

## Step 4 — In-process modules

These are **not tools**. The model never sees them. They exist so the five tools share one implementation of hard problems.

### 1. `auth_session`

**Single responsibility:** Obtain, cache, and attach credentials for Portfolios REST and SOAP. Refresh on expiry and on 401. Push the current token onto long-lived clients so a later fetch cannot leave a stale Authorization header.

**Consumers:** all five proposed tools.

**Replaces:** `oauth.py` + `PlanviewClient` header injection + SOAP session header refresh. OKR token manager is gone.

---

### 2. `rate_limit_retry`

**Single responsibility:** Retry transient transport failures (429, 502, 503, 504, timeouts, SOAP `TransportError`) with exponential backoff. Do **not** retry 400/404/validation or successful partial batches.

**Consumers:** all five proposed tools.

**Replaces:** duplicated tenacity decorators in `client.py` and `soap_client.py`, and the gap where SOAP writes skip `make_soap_request` entirely.

---

### 3. `soap_codec`

**Single responsibility:** WSDL bind, DTO / `ArrayOf*` construction, PascalCase+sort, zeep object → JSON, OpenSuite Successes/Failures/Warnings → a uniform `{items: [{status, key, dto, error}]}` result. Never decide business policy (idempotency, confirm flags).

**Consumers:** `manage_tasks`, `manage_financial_plan` (and `manage_project` when it seeds default tasks).

**Replaces:** `_parse_opensuite_result` / `_handle_soap_result` / `_convert_zeep_*`, `filter_and_sort_fields`, TaskDto2 serialization fallbacks, FinancialPlan ArrayOf wrapping.

---

### 4. `error_taxonomy`

**Single responsibility:** Map HTTP status, SOAP fault, and OpenSuite failure codes to a small set of model-facing errors: `auth`, `not_found`, `validation`, `rate_limited`, `conflict` (lifecycle/blocked field), `partial`, `unavailable`. Each error includes `retryable`, `what_to_change`, and `already_persisted` when a write partially landed.

**Consumers:** all five proposed tools.

**Replaces:** `exceptions.py` plus one-off guidance strings in financial upsert/read, work 405 handling, and project field isolation.

---

### 5. `pagination`

**Single responsibility:** Walk `limit`/`offset` (or SOAP key chunks) until exhausted or a caller-supplied cap. Return `{items, next_offset, truncated}`. Never fetch related resources (that's the tool's job).

**Consumers:** `manage_tasks` delete (chunk of 50); `inspect_work` if/when work list paging exists (today it does not — the module should surface `truncated=true` when the API likely clipped).

---

### 6. `key_uri`

**Single responsibility:** Parse and mint Planview key URIs (`key://2/$Plan/{id}`, `ekey://`, `search://`, account/period/version keys). Convert `project_id` ↔ entity key. Reject malformed keys before they hit SOAP.

**Consumers:** `manage_tasks`, `manage_financial_plan`, `manage_project` (FatherKey for default tasks).

**Replaces:** `validate_task_key` plus scattered `f"key://2/$Plan/{id}"` string builds.

---

### 7. `partial_write`

**Single responsibility:** Apply a multi-field PATCH as all-or-report: either isolate **without leaving silent success** (dry-run isolation is impossible on this API, so the contract is: return which fields persisted) or refuse to isolate and return the original 400 with a field-catalog hint.

**Consumers:** `manage_project` (`update`), `inspect_work` (`update`).

**Replaces:** the copy-pasted field-isolation loops that currently persist N−1 fields then raise.

---

Modules the user asked to expect, mapped:

| Expected | Proposed name |
|---|---|
| Auth/session handling | `auth_session` |
| Rate limiting | `rate_limit_retry` |
| SOAP envelope + XML↔JSON | `soap_codec` |
| Error taxonomy | `error_taxonomy` |
| Pagination | `pagination` |
| (extra, justified) | `key_uri`, `partial_write` |

---

## Step 5 — Failure modes

### `manage_project`

| | |
|---|---|
| **Partial success** | `create` + default tasks: project exists, 0–5 tasks missing (today this is silent). `update` with field isolation: some fields saved, then an error is raised — **already a live bug**. `delete` is all-or-nothing at the HTTP layer. |
| **What a retry does** | `create` without an external key: **second project**. `update`: reapplies same PATCH (generally safe). `delete`: 404 on retry. `get`/`fields`: safe. |
| **Idempotent?** | get/fields: yes. update: mostly. delete: yes if 404 is treated as success (today it is not). create: **no**. |
| **Error the model needs** | `validation` with the exact blocked field ID and "lifecycle-controlled — omit it". `not_found` with the project id. On create: missing `description` / `parent.structureCode`. |
| **Two-pass** | **Yes — create-then-connect:** REST `POST /projects` then SOAP `Create` for default tasks. Must return `{project, tasks: {created, failed[]}}` and never hide task failure. Field isolation is a second mutating pass — replace with `partial_write`. |

### `inspect_work`

| | |
|---|---|
| **Partial success** | `wbs`: empty or missing root → `{error: project not found in work items}` (today). Filter-variant retries may succeed on a different interpretation of the filter. `update` isolation same as project. |
| **What a retry does** | Reads: safe. `update`: same as project PATCH. |
| **Idempotent?** | wbs/get/list: yes. update: mostly. |
| **Error the model needs** | On 405: `conflict` — "this instance cannot PATCH /work; use `manage_project` for PPL nodes." On empty WBS: `not_found` plus "filter returned no nodes", not a successful empty tree. |
| **Two-pass** | `wbs` is read-compose, not create-then-connect. `update` isolation is a mutating two-pass if kept. |

### `manage_tasks`

| | |
|---|---|
| **Partial success** | SOAP Create/Delete are **not atomic**. Batch already returns per-item status. Single create/delete currently **raise** if OpenSuite reports any failure (`_handle_soap_result`), hiding siblings in a batch-of-one. |
| **What a retry does** | Create **without** `ekey://`: **duplicate tasks**. Create **with** ekey: closer to upsert (instance-dependent). Delete retry: missing keys fail; succeeded keys must not be resent. |
| **Idempotent?** | read: yes. delete: yes if missing-key is success. create: **only with caller-supplied ekey**. |
| **Error the model needs** | Per item: `{description, key, status, error}`. On FatherKey miss: `not_found` "parent work key invalid — use `key://2/$Plan/{structureCode}`". On SOAP null DTO: `success` with `echo_incomplete: true` and instruction to `read` — do not treat null dates as "create failed". |
| **Two-pass** | No create-then-connect. Serialization fallbacks (dict vs DTO vs ArrayOf) are internal retries of the **same** Create, not two operations — `soap_codec` should pick one path. |

### `manage_financial_plan`

| | |
|---|---|
| **Partial success** | Upsert: SOAP may persist lines and return empty `Lines`. Copy dry-run: no write. Copy confirm: Read(s) succeed, Upsert fails → **nothing copied** (good) unless Upsert itself partially accepts lines ("No editable lines" = zero writes). Discover: may return **reference** or **config** data labeled as the target — today `Source` is only set on the config path; reference fallback can look like the target's plan. |
| **What a retry does** | Read/discover: safe. Upsert: intended idempotent (same lines). Copy confirm: re-upsert same remapped lines — safe-ish; scale_factor applied twice if the caller retries after success without checking. |
| **Idempotent?** | read/discover: yes. upsert: yes by design. copy confirm: yes if treated as upsert. |
| **Error the model needs** | `validation` "No editable lines" with **the account/period keys that were sent** and `action=discover` as the next call. `not_found` "plan does not exist yet — upsert will create it; don't retry read." Never tell the model the write failed because the echo was empty. |
| **Two-pass** | **Yes — copy is a pipeline:** GET project ×2 → SOAP Read reference → SOAP Read target (or discover) → SOAP Upsert. Dry-run must be the default. Confirm is the write. Discover is a fallback chain (target → reference → config), not a second user-visible tool. |

### `test_connection`

| | |
|---|---|
| **Partial success** | Config can warn (empty tenant) and still fetch a token. Token OK + ping 401 is the important split. |
| **What a retry does** | Force-refreshes a new client_credentials token, then pings with that same token on a dedicated client (not the pooled REST client). |
| **Idempotent?** | Yes (reads + token issue). Issuing a new token may invalidate an older one on the Planview side — pooled clients must pick up the new header, which they now do on every `get_client()`. |
| **Error the model needs** | Structured `checks[]` plus `code`/`hint`: `config` (URL/`/polaris`, JWT-as-secret), `invalid_credentials` / `token_bad_request`, `ping_unauthorized` (tenant). Never "Invalid API key". |
| **Two-pass** | Token then ping. Both results are in the same response. |

---

## Step 6 — Output

### Current vs proposed

**21 → 5** model-facing tools (OKRs already pulled).

| Proposed tool | Spoken jobs | Old tools absorbed |
|---|---|---|
| `test_connection` | Is this MCP connected? Why did OAuth fail? | `oauth_ping` |
| `manage_project` | Create / update / get / delete a project; discover writable fields | `get_project`, `create_project`, `update_project`, `delete_project`, `list_field_reference`, `get_project_attributes` |
| `inspect_work` | Show WBS; get/list/patch a work node | `get_project_wbs`, `list_work`, `get_work`, `update_work`, `get_work_attributes` |
| `manage_tasks` | Add / read / delete tasks (single or many) | `create_task`, `batch_create_tasks`, `read_task`, `delete_task`, `batch_delete_tasks` |
| `manage_financial_plan` | Show financials; write lines; copy from a reference project | `read_financial_plan`, `upsert_financial_plan`, `discover_financial_plan_info`, `load_financial_plan_from_reference` |

**Pulled (not a demo job):** OKR tools.

### Old → new mapping table

| Old tool | New tool | Notes |
|---|---|---|
| `oauth_ping` | `test_connection` | Structured config → token → ping |
| `get_project` | `manage_project` | `action=get` |
| `create_project` | `manage_project` | `action=create`; default-task seed is an explicit flag with visible partial results |
| `update_project` | `manage_project` | `action=update` |
| `delete_project` | `manage_project` | `action=delete` |
| `list_field_reference` | `manage_project` | `action=fields` |
| `get_project_attributes` | `manage_project` (internal) | Not a default action; live dump only if catalog misses |
| `get_project_wbs` | `inspect_work` | `action=wbs` (default) |
| `list_work` | `inspect_work` | `action=list` — prefer `project_id` over raw filter |
| `get_work` | `inspect_work` | `action=get` |
| `update_work` | `inspect_work` | `action=update` |
| `get_work_attributes` | `inspect_work` (internal) | Same as project attributes |
| `create_task` | `manage_tasks` | `action=create` with a one-element list |
| `batch_create_tasks` | `manage_tasks` | `action=create` |
| `read_task` | `manage_tasks` | `action=read` |
| `delete_task` | `manage_tasks` | `action=delete` with a one-element list |
| `batch_delete_tasks` | `manage_tasks` | `action=delete` |
| `read_financial_plan` | `manage_financial_plan` | `action=read` |
| `upsert_financial_plan` | `manage_financial_plan` | `action=upsert` |
| `discover_financial_plan_info` | `manage_financial_plan` | `action=discover` |
| `load_financial_plan_from_reference` | `manage_financial_plan` | `action=copy` |
| `list_objectives` | — | Pulled. Not a demo job. |
| `get_key_results_for_objective` | — | Pulled. |
| `list_all_objectives_with_key_results` | — | Pulled. |

### Module list (responsibilities)

| Module | Responsibility | Used by |
|---|---|---|
| `auth_session` | Token cache and header injection for Portfolios REST and SOAP | all 5 |
| `rate_limit_retry` | Backoff on transient HTTP/SOAP transport errors only | all 5 |
| `soap_codec` | Envelope, DTO/ArrayOf, XML↔JSON, OpenSuite itemization | `manage_tasks`, `manage_financial_plan`, `manage_project` (task seed) |
| `error_taxonomy` | Stable model-facing error codes + `already_persisted` | all 5 |
| `pagination` | SOAP chunk walks with `truncated` | `manage_tasks`, later `inspect_work` |
| `key_uri` | Parse/mint `key://` / `ekey://` / `search://` | `manage_tasks`, `manage_financial_plan`, `manage_project` |
| `partial_write` | Multi-field PATCH reporting which fields persisted | `manage_project`, `inspect_work` |

### Ranked build order (demo jobs, not API completeness)

Evidence of "what demos actually use" comes from this repo's own positioning, not telemetry:

- README **Local handles:** "Create a new project", "Add tasks", "Set up a financial plan", "Update project status", "Copy a financial plan from a reference project."
- `field_reference.py`: curated **~120 demo-relevant writable fields** (status assessments, WSJF, dates) — the update-project story.
- `create_project(create_default_tasks=True)` and `load_financial_plan_from_reference` are the only current JOB-shaped **write** paths built specifically for live demos.
- `test_connection` is setup **and** the first thing a coworker runs when OAuth fails. Harden it before anything else.
- Live attribute dumps (`get_*_attributes`) fight the model with hundreds of IDs; demos use the curated catalog.

**Build this order:**

| Rank | Build | Why first |
|---|---|---|
| 0 | `test_connection` + `auth_session` error taxonomy | Coworker is already hitting OAuth failures with "fresh tokens". Diagnose config vs token vs tenant ping before any write tool. **Done in this change.** |
| 1 | `manage_project` (`create`, `update`, `fields`, `get`) | Hero demo: stand up a project and set RAG/status. Absorbs the field catalog so the model stops guessing Wbs709 vs Status. |
| 2 | `soap_codec` + `key_uri` | Unblocks tasks and financials. One OpenSuite parser; one key language. |
| 3 | `manage_financial_plan` (`copy` then `read`/`discover`/`upsert`) | The wow path in README ("copy from reference"). Dry-run default stays. Label fallback source so the model never upserts against the wrong project's accounts. |
| 4 | `manage_tasks` (`create` list, then `read`/`delete`) | "Add tasks to this project." Mint ekeys by default so retries don't duplicate. Collapse single/batch. |
| 5 | `inspect_work` (`wbs` first) | Verify tasks landed; not the opening move. Kill raw filter as the default. |
| 6 | `partial_write` | Fix the silent partial PATCH on project/work update — needed once `manage_project` update is live. |

**Do not build (as tools):** OKRs, live attribute dumps, `create_task` vs `batch_create_tasks` as twins, `list_work` as a filter DSL, resource helpers.

---

## Design rules this audit commits to

1. **If a person wouldn't say the tool name out loud, it isn't a tool.** `batch_delete_tasks` is SOAP. `manage_tasks` is the job.
2. **Batching, WSDL, filter variants, and pagination are modules.** They shrink latency; they must not multiply `list_tools`.
3. **Companion-server reads stay with Anvi Prod** for portfolio search/list. Local `get` exists to **verify writes**, not to re-implement catalog browse.
4. **Two-pass operations return both passes.** Create-then-seed-tasks and copy-financials-then-upsert are first-class in the response, not logged-and-forgotten.
5. **SOAP success with null echo is success.** The model is told to `read` if it needs values, not to retry create.

This document is analysis only. No code was changed.
