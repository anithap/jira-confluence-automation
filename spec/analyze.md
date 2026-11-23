# Task Complexity, Risk, and Dependency Analysis

**Analyzed files:** [tasks.md](tasks.md), [plan.md](plan.md),
[specification.md](specification.md), [constitution.md](constitution.md),
[clarify.md](clarify.md)

Complexity ratings:

- **Low:** Small, localized setup or contract implementation.
- **Medium:** Multiple modules or cross-service integration.
- **High:** Significant architecture, concurrency, security, or data-integrity
  work.

## Phase 1: Backend Tasks

| Task | Complexity | Main risks | Dependencies | Notes |
|---|---:|---|---|---|
| BE-001: PostgreSQL Docker service | Medium | Secret exposure, volume/port conflicts, platform differences | None | The repository currently contains only a placeholder Compose file, so image, env, volume, healthcheck, and networking details are missing. |
| BE-002: Migration tooling | Medium | Incompatible migration startup, partial schema deployment | BE-001 | Requires an exact migration framework and rollback policy that are not specified. |
| BE-003: Database entities | High | Report replacement inconsistency, missing constraints, PII retention | BE-002 | The entity names exist only in specs. Unique constraints and retention policies need implementation decisions. |
| BE-004: Backend skeleton | High | Framework setup drift, exposed secrets, inconsistent error shape | BE-001 | Package manifest is empty, so Express dependencies and scripts are not yet defined. |
| BE-005: Repository interfaces | High | SQL injection, transaction leakage, partial latest-report updates | BE-003, BE-004 | Needs a transaction abstraction and clear latest-report replacement algorithm. |
| BE-006: Configuration/health routes | Medium | Configuration leakage, inconsistent readiness semantics | BE-004, BE-005 | `GET /health` should not treat database and Jira availability as one unqualified state. |
| BE-007: API report skeleton | High | Concurrent refreshes, underdefined DTOs, HTML response behavior | BE-004, BE-005 | Refresh, run, error, and HTML status contracts should be finalized before implementation. |

## Phase 2: Frontend Tasks

| Task | Complexity | Main risks | Dependencies | Notes |
|---|---:|---|---|---|
| FE-001: React/Vite shell | Medium | Dependency/version drift, empty package manifest | None | `frontend/package.json` is empty; React 18, Vite, test, lint, and build dependencies are missing. |
| FE-002: Shared UI components | Medium | Accessibility gaps, unclear unavailable-state design | FE-001 | Component visual details are not specified in sufficient detail for high-fidelity implementation. |
| FE-003: Frontend routing | Low | Broken navigation, stale route state | FE-001 | Route names and `/` behavior should be confirmed as implementation contracts. |
| FE-004: Configuration status screen | Medium | Secret rendering, overloaded configuration response | BE-006, FE-002, FE-003 | The UI must distinguish non-secret metadata from secret presence. |
| FE-005: HTML report preview | Medium | Unsafe HTML rendering, iframe/CSP risk | BE-007, FE-002, FE-003 | Preview/download method, CSP, filename, and navigation behavior are not fully specified. |

## Phase 3: Feature Tasks

| Task | Complexity | Main risks | Dependencies | Notes |
|---|---:|---|---|---|
| FI-001: Configuration and secrets | High | Missing or duplicate env contracts, secret persistence | BE-004, BE-005 | No environment template or secret-store implementation is provided. |
| FI-002: Jira client | High | Authentication failure, retries, pagination, Jira API differences | FI-001 | Needs Jira API library choice or HTTP client, timeouts, rate limits, and retry limits. |
| FI-003: Board and active sprint | Medium | No active sprint, ambiguous sprint, wrong board/project | FI-002 | Board ID and story-point field are still deployment prerequisites. |
| FI-004: Jira issue normalization | High | Schema variation, incomplete payloads, invalid custom fields | FI-003 | Mandatory/optional field validation should be converted into a formal schema. |
| FI-005: Status/issue metrics | Medium | Wrong status category mapping, empty sprint, timezone mismatch | FI-004 | Status-category names and unknown-category handling need exact fixtures. |
| FI-006: Story-point metrics | Medium | Invalid values, rounding, decimal precision, missing denominator | FI-004 | Decimal precision and unavailable-total behavior need exact test vectors. |
| FI-007: Accomplishments/blockers | Medium | Incorrect threshold boundary, hidden blocker history, PII | FI-004, FI-005 | Exact update-time timezone and configured status behavior need test fixtures. |
| FI-008: Deterministic summary | Medium | Nondeterministic narrative, unsupported inferences | FI-005, FI-006, FI-007 | The previous CLI template conflicts with web-app DTO/content conventions. |
| FI-009: Standalone HTML report | High | XSS, unsafe links, stale warning, CSS/layout defects | FI-005 to FI-008 | No HTML template or renderer package exists yet. |
| FI-010: Atomic refresh replacement | High | Database/report mismatch, partial updates, concurrency | BE-005, FI-003 to FI-009 | Requires transaction semantics and an explicit source snapshot timestamp. |
| FI-011: Report API and HTML preview | High | DTO mismatch, MIME/CSP issues, stale data exposure | BE-007, FI-010 | API response schemas, status codes, and HTML headers need exact documentation. |

## Phase 4: Integration and Testing Tasks

| Task | Complexity | Main risks | Dependencies | Notes |
|---|---:|---|---|---|
| IT-001: Frontend/backend integration | High | Contract drift, stale state, CORS/auth mismatches | FE-004, FE-005, BE-006, BE-007 | Requires a shared or generated API contract to reduce DTO drift. |
| IT-002: Backend unit tests | Medium | Tests restating implementation, missing edge cases | FI-002 to FI-009 | Existing Python tests do not verify this Node/Express implementation. |
| IT-003: Backend integration tests | High | PostgreSQL setup, Jira fixtures, test isolation | BE-005, FI-010 | No test database infrastructure or fixture repository is specified. |
| IT-004: Frontend tests | Medium | Flaky browser tests, incomplete state coverage | FE-002 to FE-005, IT-001 | Test framework and browser support are not declared. |
| IT-005: Docker Compose end-to-end | High | Service startup order, volume/network issues, migration timing | BE-001 to BE-007, FE-001 to FE-005 | Compose currently contains only a placeholder. |
| IT-006: Security/reliability checks | High | Secret leakage, XSS, unsafe atomic failure behavior | FI-001, FI-002, FI-009, FI-010 | No security scanning, CSP policy, or threat model is implemented in tasks. |
| IT-007: Performance/acceptance | High | Live Jira instability, <5-minute threshold, missing data | IT-002 to IT-006 | Acceptance needs both deterministic fixtures and an optional live smoke test. |

## Cross-Document Gaps

### G1. Fundamental architecture contradiction

The specification has later sections that state Express, React, and PostgreSQL
are out of scope for the prototype. The plan and tasks replace that decision
with a full React/Express/PostgreSQL web application.

**Required action:** Choose the web application as the authoritative scope or
restore the specification's CLI-only prototype. If the web application wins,
update the specification's sections 9-11, 13.6, 14, 15-17, and out-of-scope
statements so they match the plan/tasks.

**Severity:** Critical

### G2. Confluence scope remains inconsistent

The constitution describes Jira/Confluence synchronization, but the plan and
tasks exclude Confluence reads and writes. The specification clarifies
Confluence is out of scope, while project identity still presents the product
as Jira/Confluence automation.

**Required action:** Rename or scope the MVP as Jira automation and state
Confluence as a future extension, or add separate Confluence requirements.

**Severity:** High

### G3. Authentication and authorization are not implementable

Tasks mention an HTTP authentication policy but do not define users, roles,
login mechanism, session/cookie behavior, or API authorization.

**Required action:** Decide local-only, reverse-proxy, session, OAuth/Jira
OAuth, or a single-user trust model. Add endpoints and UI behavior for denied
access.

**Severity:** Critical

### G4. API contracts are incomplete

The specification defines example JSON and endpoints, but tasks still need:

- Exact HTTP status codes
- Standard error body
- Request/response schemas
- CORS origin policy
- No-report and stale-report behavior
- Concurrent refresh behavior
- HTML MIME, CSP, and disposition behavior

**Severity:** High

### G5. Database schema details are incomplete

Tables and relationships are described conceptually, but tasks do not identify:

- Exact column types and constraints
- Migration framework
- Latest-row uniqueness mechanism
- Refresh-run retention/purge policy
- Database availability behavior
- PII/assignee storage policy
- Snapshot consistency transaction boundary

**Severity:** Critical

### G6. Missing Docker and package artifacts

The repository has placeholders:

- `docker-compose.yml` contains no services.
- `backend/package.json` is empty.
- `frontend/package.json` is empty.
- No backend source files or frontend source files are present.

**Required action:** Add these setup tasks or explicitly include artifact
creation acceptance criteria in BE-001, BE-004, and FE-001.

**Severity:** Critical

### G7. Missing dependency graph tasks

Tasks FE-001 and BE-001 are independent, but implementation order in the plan
does not add a shared environment/bootstrap task. IT-005 depends on all setup
tasks but can begin only after package scripts and container names exist.

**Required action:** Add root scripts or a documented Compose command for
build, migration, test, and health operations.

**Severity:** Medium

### G8. Scheduled refresh contradicts the web plan

The specification retains manual and Windows scheduled execution. The web plan
and tasks have no scheduled-job task and describe only API-triggered manual
refresh.

**Required action:** Add scheduled refresh infrastructure or remove scheduling
from the web scope. If retained, specify process ownership, timezone, lock,
retry, missed-run, and database run-source behavior.

**Severity:** High

### G9. Jira completeness rules are underdefined

Tasks say partial required data stops generation but do not list every mandatory
Jira field in machine-readable form.

Required fields should at minimum include:

- Issue key
- Summary
- Status name
- Status category
- Updated timestamp
- Jira web URL
- Project key
- Story-point custom field value or explicit missing marker

**Severity:** High

### G10. Story-point and numerical rules need fixtures

Tests need exact cases for:

- Missing/null values
- Invalid strings
- Negative values
- Zero
- Decimals
- Values above two displayed decimal places
- Empty sprint
- Missing completed or remaining points
- Rounding mode

**Severity:** High

### G11. HTML/report path is not aligned

The specification says standalone HTML may be local, while the web plan proposes
HTML preview/download over Express. The report file path, file persistence,
and database copy relationship are unspecified.

**Required action:** Decide whether Express generates an HTTP artifact, the
latest HTML is stored on disk, or HTML is generated at request time.

**Severity:** High

### G12. Missing acceptance for no-report state

BE-007 and FE-003 mention no-report behavior, but there is no task for the
first successful refresh or initial database state.

**Required action:** Add initial-state data, migration seed behavior, and UI
empty-state copy.

**Severity:** Medium

### G13. Concurrency behavior is incomplete

BE-007, FI-010, and the spec mention concurrency, but no task defines lock
ownership, lock lifetime, stale lock cleanup, status code, or retry behavior.

**Required action:** Add a database advisory lock or unique active-run
constraint and document timeout/recovery.

**Severity:** High

### G14. Missing observability task

The plan requires request IDs and credential-safe logs, but tasks do not add a
dedicated logging/metrics/health validation task.

**Required action:** Add structured logs, redaction tests, refresh timing,
Jira API status metrics, and health dashboard behavior.

**Severity:** Medium

### G15. Missing Confluence boundary validation

Confluence is not implemented, but no automated or code-review rule prevents
later accidental writes. There is no feature flag or integration boundary task.

**Required action:** Confirm read-only or disabled boundary, add a
configuration feature flag, and test that no Confluence credentials or endpoints
are registered.

**Severity:** Medium

### G16. Existing Python implementation is not reconciled

The repository has `generate_sprint_report.py` and Jira helper tests. The web
plan/tasks do not say whether the Python implementation is reused, migrated,
ignored, or replaced.

**Required action:** Add a migration or decommission task and avoid duplicate
Jira/report implementations.

**Severity:** High

## Missing Artifacts

The following files or artifacts should be added before implementation:

- Backend and frontend package manifests and lockfiles
- Backend TypeScript/JavaScript lint and test configuration
- Frontend test, lint, build, and routing configuration
- Docker Compose service definitions and `.env.example`
- Database migration framework and initial migrations
- API OpenAPI or equivalent schema
- Shared error and response DTO definitions
- Jira integration adapter and fixture set
- PostgreSQL repository test setup
- React component and state test setup
- HTML report template/CSP policy
- Windows scheduling task only if web scheduling remains in scope
- Threat model and secrets handling runbook
- Accessibility test target and browser matrix
- Observability/redaction runbook
- Migration/decommission plan for existing Python report code

## Contradiction Matrix

| Area | Constitution/specification | Plan/tasks | Severity |
|---|---|---|---|
| Delivery mode | Specification later says CLI-only prototype | Web app with React/Express/PostgreSQL | Critical |
| Confluence | Constitution says Confluence integration; specification says out of scope | No Confluence implementation | High |
| Scheduling | Specification requires Windows scheduled task | Plan/tasks omit schedule implementation | High |
| Data storage | Specification later says PostgreSQL out of scope | Plan/tasks require PostgreSQL | Critical |
| Existing Python | Specification says Python prototype implementation exists | Web plan/tasks do not reconcile it | High |
| UI | Specification says React UI is out of scope later | Plan/tasks require React UI | Critical |
| API | Specification says REST API is out of scope later | Plan/tasks require Express endpoints | Critical |

## Recommended Implementation Order

The implementation should prioritize small setup and contract decisions that
unlock the largest downstream area. High-risk tasks are not necessarily
deferred because they are difficult; they are deferred until their
dependencies and interfaces are stable.

### 1. Resolve scope and architecture decisions

Complete the low-cost documentation decisions before code:

1. Reconcile the web application scope with the CLI-only prototype text.
2. Confirm that Confluence is outside the MVP.
3. Decide local-only deployment and the authentication/authorization model.
4. Decide whether Windows scheduled refresh remains in scope.
5. Decide whether PostgreSQL is authoritative for report state or whether HTML
   remains a separate report artifact.

These decisions remove contradictions that would otherwise require rework across
the database, API, UI, and tests.

### 2. Create low-risk project skeletons

After scope is fixed, perform independent setup tasks with immediate feedback:

1. FE-001: Create the React/Vite application shell.
2. BE-001: Add the PostgreSQL Docker service.
3. BE-004: Create the backend application skeleton.
4. BE-002: Add migration tooling.
5. Add package scripts for install, build, lint, test, migrate, and startup.

These tasks provide fast feedback and unblock package, Docker, and framework
validation before Jira logic is added.

### 3. Freeze contracts and schemas

Complete these low/medium-risk artifacts next:

1. Add the API/OpenAPI-style contract and shared DTO/error definitions.
2. Define exact HTTP status codes, error bodies, MIME types, and HTML headers.
3. Define database migrations, exact columns, constraints, and indexes.
4. Define the active-run/concurrency strategy and stale-run cleanup.
5. Define environment-variable names and add `.env.example`.
6. Define Jira fixture schemas and missing-field behavior.

Freezing contracts prevents repeated changes in the Jira, repository, React, and
test implementations.

### 4. Implement persistence foundations

Resolve database dependencies before feature logic:

1. BE-003: Create database entities.
2. BE-005: Implement repository interfaces and transaction support.
3. BE-006: Implement health and configuration routes.
4. BE-007: Implement report/run route contracts.

This establishes the transaction boundary needed by refresh and release testing.

### 5. Build frontend foundations

Once API contracts exist:

1. FE-002: Add shared UI components and unavailable-state conventions.
2. FE-003: Add routing and route-level error/loading behavior.
3. FE-004: Integrate configuration status.
4. FE-005: Integrate HTML preview behavior.
5. IT-004: Add focused frontend state tests.

Frontend foundation work is lower risk because it can proceed against fixtures
before live Jira retrieval is complete.

### 6. Implement Jira integration and metrics incrementally

Deliver feature slices in dependency order:

1. FI-001: Configuration and secret handling.
2. FI-002: Jira client.
3. FI-003: Board and active-sprint retrieval.
4. FI-004: Jira issue normalization.
5. FI-005: Issue/status metrics.
6. FI-006: Story-point metrics.
7. FI-007: Accomplishments and blockers.
8. FI-008: Deterministic summary.

Unit tests should accompany each step rather than wait until all Jira code is
complete.

### 7. Implement report persistence and presentation

After metrics are stable:

1. FI-009: Standalone HTML rendering.
2. FI-010: Atomic refresh and database replacement.
3. FI-011: Report API and HTML preview.
4. IT-001: Connect frontend screens to backend flows.

These tasks have high data-integrity and security impact, so their dependencies
and fixtures must be complete first.

### 8. Perform integration and release validation

After feature slices pass:

1. IT-002: Backend unit tests.
2. IT-003: PostgreSQL/Jira fixture integration tests.
3. IT-005: Docker Compose end-to-end startup.
4. IT-006: Security and reliability checks.
5. IT-007: Performance and acceptance verification.

These tasks should be release gates, not early implementation prerequisites.

### 9. Resolve remaining scope artifacts

During or after core implementation:

1. Reconcile or decommission the existing Python implementation.
2. Add scheduled refresh only if scheduling remains in scope.
3. Add observability, metrics, and redaction tests.
4. Document the Confluence disabled boundary.
5. Add accessibility and browser verification.

These items add scope or operating controls but do not unlock the core report
feature.

## Low-Risk, High-Gain Sequence

The earliest implementation batch should contain:

1. Scope reconciliation and architecture decision.
2. Contract and environment-template creation.
3. React/Vite shell.
4. Backend Express skeleton.
5. PostgreSQL Docker and migrations.
6. API DTO/error definitions.
7. Database repositories.
8. Frontend fixture-driven report components.

This batch has comparatively low runtime risk, produces fast visible progress,
and prevents cross-layer rework.

## Defer Until Dependencies Exist

Do not start the following work before the listed dependencies are stable:

| Task | Defer until |
|---|---|
| FI-009: HTML report | Jira DTO, metrics DTO, escaping policy, and stale-report contract |
| FI-010: Atomic refresh | Transaction abstraction, report schema, active-run strategy |
| FI-011: Report API | Report DTO, database replacement, HTML content contract |
| IT-003: Backend integration tests | Migration framework and repository implementation |
| IT-005: Docker end-to-end | Package scripts, Compose services, migrations, and frontend API URL |
| IT-006: Security checks | Authentication policy, secret handling, HTML/CSP policy |
| IT-007: Acceptance | Unit/integration suites and Docker end-to-end pass |

## Per-Task Completion Risks

Implementation can begin for BE-001 and FE-001 as isolated setup work, but
release work should be gated until the scope and contract decisions above are
resolved. BE-003/BE-005/FI-010/IT-003 are the highest data-integrity risks.
FI-002/FI-004/FI-009/IT-006 are the highest Jira/security risks. IT-005 and
IT-007 are release blockers.
