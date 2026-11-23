# Jira/Confluence Automation Constitution

## Purpose

This constitution defines the non-negotiable principles and engineering
standards for the Jira/Confluence automation project. Specifications,
implementation plans, source code, tests, and documentation must comply with
it.

## Project Identity

- **Project name:** Jira/Confluence Automation
- **Purpose:** Retrieve Jira sprint and issue data, create human-approved
  status reports, and synchronize approved Jira or Confluence content through
  secure, auditable automation.
- **Target users:** Team managers and delivery stakeholders who need accurate
  sprint health, blockers, accomplishments, and status updates. Jira and
  Confluence administrators authorize integrations and any write operations.

## Technology Baseline

- Frontend: React 18.x with Vite
- Backend: Node.js v26.13.1 with Express
- Package manager: npm 11.20.0
- Runtime manager: nvm 1.2.2
- Database: PostgreSQL 15.x
- Infrastructure: Docker 29.9.3 and Docker Compose
- External integrations: Jira Cloud and Confluence Cloud REST APIs
- Configuration: Environment variables and local secret stores; no secrets in
  source control

Frontend and backend code must remain independently buildable and deployable
through Docker. PostgreSQL must not be run as an embedded or in-memory
replacement in production-like environments.

The Express, Vite, React, Docker Compose, and supporting package versions not
listed above must be recorded in package manifests and lockfiles. The application
must use the repository-pinned versions rather than an unrecorded global
version.

## Folder Structure Conventions

The implementation must follow a consistent top-level layout:

```text
spec/                 Specifications and the project constitution
frontend/             React 18 and Vite application
  src/
    components/       Reusable presentation components
    features/         Feature-oriented workflows and state
    pages/            Route-level views
    services/         API client modules
    styles/           Shared styles and theme definitions
  public/             Static public assets
backend/              Node.js and Express application
  src/
    config/           Environment and application configuration
    integrations/     Jira and Confluence API clients
    services/         Business rules and synchronization workflows
    controllers/      HTTP request and response handling
    routes/           Express route registration
    repositories/     PostgreSQL persistence access
    middleware/       Authentication, validation, logging, and errors
    models/           Domain and persistence models
  tests/              Backend unit and integration tests
tests/                Shared or cross-service tests
tools/                Operational and validation utilities
work/                 Generated reports and working artifacts
```

- Feature code must remain close to its feature rather than accumulating in
  shared folders.
- Integration-specific types and rules must stay inside `integrations/`.
- Database SQL and migrations must not be embedded in route or controller files.
- Configuration and secrets must not be duplicated across source directories.
- Each feature or integration should have a colocated test module or a clearly
  corresponding test file.

## Coding Standards

### Naming

- Use `PascalCase` for React components and component filenames.
- Use `camelCase` for JavaScript variables, functions, methods, and object
  properties.
- Use `UPPER_SNAKE_CASE` for environment variables and exported constants.
- Use `kebab-case` for route paths, documentation filenames, and package scripts.
- Use descriptive Jira and Confluence domain names, such as `JiraIssue`,
  `ConfluencePage`, `sprintReport`, or `publishConfluencePage`.
- Use `Id` consistently in API-facing and database identifiers, for example
  `boardId`, `issueId`, and `pageId`.
- Avoid abbreviations except established domain terms and widely understood
  names such as `API`, `URL`, `HTTP`, and `HTML`.
- Boolean names must describe state or intent, for example `isApproved`,
  `hasMissingData`, or `canPublish`.

### File Organization

- Keep React components focused on one responsibility and extract reusable logic
  into hooks or services.
- Export one primary component per component file.
- Keep Express route files limited to route registration and handler delegation.
- Keep API calls, normalization, calculations, persistence, and rendering in
  separate modules.
- Use explicit imports and avoid circular dependencies.
- Keep functions small enough to test through observable behavior; extract
  complex Jira or Confluence transformations from HTTP handlers.
- Use dependency injection or service factories for external integrations.
- Treat configuration as read-only after startup.

### Formatting and Error Handling

- JavaScript and JSX must use the repository formatter and lint configuration.
- Prefer immutable data updates and no mutation of API response objects.
- Validate inputs at system boundaries.
- Do not swallow errors. Return or record a concise operation-specific error
  without secrets or authorization headers.
- Prefer typed contracts or validation schemas for persisted and API-bound
  data.

## Core Principles

### 1. Specification Is the Source of Truth

Implementation behavior must be traceable to a written requirement or
acceptance criterion. Ambiguous Jira fields, status mappings, permissions, or
delivery behavior must be clarified before implementation. Generated artifacts
must not invent missing data or represent inferred values as factual.

### 2. Deterministic and Auditable Automation

Reports and synchronized content must use only resolved source data. Calculations
must be explicit, repeatable, and testable. Data timestamps, source identifiers,
and configuration provenance must be retained where users consume generated
content.

### 3. Least-Privilege Access

Jira and Confluence credentials must grant only the permissions required by the
automation. API tokens and account secrets must be loaded from environment
variables or a local secret store and must never appear in logs, source code,
browser output, or committed configuration.

### 4. Read-before-Write

Jira or Confluence mutations require an explicit approved requirement, clear
authorization, and a corresponding audit trail. Read-only functionality must
remain read-only. Bulk writes must be dry-runable and must fail safely rather
than partially applying an operation.

### 5. Human Approval for External Actions

Generated reports, Jira updates, and Confluence publications must be drafts
until a human reviews them, unless an existing specification explicitly
requires a fully automated operation. Automation must not silently distribute
content outside the approved user, project, or workspace.

### 6. Reliability and Data Integrity

Source responses must be complete and validated before calculations or writes
are performed. Failures must stop the affected operation and preserve the last
known-good result when practical. Retries must be bounded, and API pagination
must be used for list retrieval. Partial or stale data must be clearly labeled.

### 7. Security and Safe Rendering

All external text must be escaped before rendering into HTML or React. API
traffic must use HTTPS. The application must validate inputs, prevent
authorization bypasses, apply appropriate CORS and HTTP security settings, and
avoid exposing internal API details or credentials in client responses.

### 8. Separation of Concerns

The system must separate:

- Jira and Confluence API clients
- Source-data normalization and validation
- Calculation and synchronization rules
- Persistence
- HTTP routes and controllers
- React presentation components

Service boundaries must keep integrations replaceable and must allow unit tests
to run without live Atlassian credentials.

### 9. Accessibility and Usable Errors

The frontend must use semantic HTML, keyboard-accessible controls, visible
focus states, responsive layouts, and clear status feedback. API and UI errors
must describe the failed operation and a safe next step without exposing secrets
or implementation details.

### 10. Testability and Verification

Behavioral changes require focused automated tests. Tests must cover success,
failure, missing-data, pagination, authorization, and write-failure cases.
Unit tests must not depend on live Jira or Confluence services. Integration
tests must isolate test workspaces and must not mutate production Atlassian
data.

## Architecture Requirements

- Use a React 18 application built with Vite for the frontend.
- Use Express route handlers with focused controllers or services for backend
  HTTP behavior.
- Use PostgreSQL 15 as the persistence layer.
- Use Docker Compose for repeatable local development and service startup.
- Use transactions for database operations that require atomicity.
- Isolate all Atlassian API calls behind integration modules.
- Keep generated reports or documents reproducible from the same source data
  and configuration.
- Prevent credential-bearing configuration from being returned to the frontend
  or persisted in application snapshots.

## Jira and Confluence Rules

- Jira issues, fields, status categories, and custom field identifiers must be
  resolved or configured explicitly.
- Jira pagination must cover all required records.
- Confluence pages must identify the target space and page explicitly.
- Confluence content must preserve source-page identity or a clear source
  reference.
- Atlassian text must be escaped or sanitized according to the rendering context.
- Synchronization must be idempotent where practical and must detect source or
  destination changes before overwriting content.
- No Jira or Confluence data may be edited or published unless the requirement
  explicitly permits that operation.

## Configuration Rules

Configuration must define environment-specific values such as:

- Atlassian base URLs
- Jira board, project, or field identifiers
- Confluence space or page identifiers
- API credential environment-variable names
- Database connection settings
- Output or publication destinations
- Allowed write operations
- Human-approval requirements
- Retry limits and timeouts

Missing configuration must fail early with an actionable error. Candidate values
must not be silently promoted to production settings.

## Data and Persistence Rules

- Missing values must remain missing or be marked unavailable; they must not be
  replaced by guessed, zero, or fabricated values.
- Database migrations must be reviewed and backward-compatible when feasible.
- PII and Atlassian identifiers must be stored only when required by the
  specified use case.
- Records should retain source identifiers and refresh or modification
  timestamps when relevant.
- Destructive operations and purge behavior require an explicit requirement.

## Quality Gates

Before a change is accepted, it must:

1. Trace back to a specification or approved issue.
2. Pass focused unit and integration tests.
3. Pass frontend and backend build or type checks.
4. Avoid credential or secret exposure.
5. Preserve existing data after failures where atomicity is required.
6. Preserve or improve accessibility.
7. Document configuration and operational behavior that changed.
8. Confirm that any Jira or Confluence write is explicitly authorized.

## Amendment Process

Amendments require:

- A documented rationale
- Affected requirements or implementation areas
- Migration or compatibility considerations
- Updated tests or validation criteria
- A clear record of the new constitution version

## Governance

This constitution supersedes conflicting implementation preferences. A
specification may add constraints, but must not weaken a security, privacy,
data-integrity, or human-approval principle. Violations must be resolved before
implementation is accepted. The team should review this constitution when the
tech stack, data sources, security model, or publication scope changes.
