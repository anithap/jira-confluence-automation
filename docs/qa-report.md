# QA Report — Jira Sprint Status Application

**Test date:** 2026-11-23
**Environment:** Windows, local Vite frontend, local Express API, Chrome
**Overall status:** All executed automated tests pass. The UI and validation flow work; an end-to-end Jira report and Docker startup remain unverified.

## Pages visited

| Page | Result |
|---|---|
| `http://localhost:5173/` | Main report setup page loaded successfully after the frontend was implemented and started. |
| Report preview | Not reached; no report was generated during this session. |

No other frontend routes were implemented or visited.

## Screenshot references

- **S1 — Main page after fixes:** [main-page.png](./screenshots/main-page.png)
- **S2 — Invalid URL validation response:** [invalid-url-validation.png](./screenshots/invalid-url-validation.png)
- **S3 — Empty-form required-field validation:** [required-fields.png](./screenshots/required-fields.png)
- **Initial blank page:** A blank-page screenshot was shown in an earlier browser-check turn, before the app existed, but was not saved as a project file. S1 documents the repaired page.

## Interactive tests performed

1. Opened the app at `http://localhost:5173/` and inspected the setup form.
2. Filled the form with dummy data, including `https://example.com`, and submitted it.
3. Confirmed the API rejected the non-Atlassian host with HTTP 400 before making a Jira request, and the page announced the reason in an accessible error alert. The captured state is S2.
4. Reloaded the app after adding its favicon and confirmed the favicon request no longer returned 404.
5. Submitted the form with required fields empty. The browser blocked submission, announced “Please fill out this field,” and sent no fetch/XHR request. See S3.

The report preview/download interaction was not reached because no real Jira report was generated.

## Visible elements inspected

The main page displays:

- “Sprint status report” heading and read-only Jira label.
- Jira site URL field.
- Board ID and project key fields.
- Jira account email and password-style API token fields.
- Story point field, blocked status, and blocker-age threshold fields.
- “Generate sprint report” submit button.
- Read-only and token-handling guidance.
- An accessible error alert after submitting invalid test data.

The preview and “Download HTML” controls only appear after successful generation; they were not exercised.

## Tests and results

| Test | Result |
|---|---|
| Load the frontend at `localhost:5173` | **Pass:** HTTP 200; page title and form rendered. |
| Backend health check at `/api/health` | **Pass:** returned `{"status":"ok"}`. |
| Submit the empty form | **Pass:** browser required-field validation blocked submission; no fetch/XHR request was sent. See S3. |
| Submit syntactically complete test data with `https://example.com` as the Jira URL | **Pass:** API returned HTTP 400 before contacting Jira; UI displayed “Report not generated” and explained that an HTTPS Atlassian Cloud URL is required. Dummy test credentials were used, not a real token. See S2. |
| Overlapping report requests | **Pass:** automated test verified that a concurrent request receives HTTP 409, then a later request succeeds after the active generation completes. |
| Backend API unit tests | **Pass:** 6 tests passed, including validation, successful mocked report generation, safe error responses, and concurrency handling. |
| Frontend production build | **Pass:** `npm run build` completed. |
| Existing Python regression suite | **Pass:** 28 tests passed. |
| Docker Compose syntax | **Pass:** `docker compose config --quiet` completed successfully. |
| Docker Compose runtime | **Blocked:** Docker Desktop’s Linux engine returned HTTP 500, so containers could not be started or tested. |
| Jira integration with a real active sprint | **Not run:** no real Jira credentials were supplied. |

## Browser console and network observations

- Initial page load showed only normal Vite connection messages and the React DevTools informational notice; no JavaScript exceptions or warnings were observed.
- The first load requested `/favicon.ico` and received 404. A local `favicon.svg` was added and linked from the page; after reload it returned 304 (cached), with no favicon error.
- The deliberately invalid form submission produced an HTTP 400 for `/api/report`. This is the expected validation response, not a JavaScript exception; the UI displayed the error.

## Bugs found

| ID | Severity | Description | Screenshot/evidence | Status |
|---|---|---|---|---|
| QA-01 | **High** | Initially, `localhost:5173` was blank/unavailable because the workspace had no frontend entry point or runnable web app. This prevented all browser-flow testing. | Initial blank capture was shown earlier in the session but was not saved. S1 shows the page after the fix. | **Fixed** |
| QA-02 | **Low** | The first rendered page requested `/favicon.ico`, which returned 404. | Initial network request `reqid=17` in the session; S1 shows the app after the favicon fix. No before-fix screenshot was saved. | **Fixed** |

The HTTP 400 for `https://example.com` is **not a bug**: it is the intended server-side rejection of an unsupported host, and the UI reports it clearly.

## Fixes applied and commit references

| Fix | Change | Commit reference |
|---|---|---|
| QA-01 | Added the React/Vite setup page and Express endpoint around the existing Python report generator, with client/server validation and report result handling. This expanded the original CLI-only prototype scope with approval. | None — no commit was created during this work. |
| QA-02 | Added `frontend/public/favicon.svg` and linked it in `frontend/index.html`. | None — no commit was created during this work. |

The backend passes the token to the Python process through its environment rather than placing it in the temporary JSON configuration. The form clears the token after a request, and unexpected backend errors are returned without internal detail. Credential handling was not verified against a real Jira site.

## Current status and remaining QA

- The local development servers are responding at `http://localhost:5173` and `http://127.0.0.1:3001`.
- The basic setup form, validation response, report API test path, and UI build are working.
- **Executed automated tests:** backend 6/6, Python 28/28, frontend production build passed.
- **Additional checks this run:** empty-form browser validation and concurrent-request handling passed; backend tests now pass 6/6.
- A successful report preview and download still need testing with approved Jira credentials and a board containing exactly one active sprint.
- Docker startup needs to be retested after the Docker Desktop Linux engine is healthy.
- PostgreSQL is included in Compose for the planned architecture but is not yet used by this report-generation flow; configuration and reports are not persisted by the web UI.
- Responsive layout and keyboard operation were implemented but not fully exercised across devices or assistive technology.

## Commands run

```text
backend: npm test                         6 passed
frontend: npm run build                  passed
python -m unittest discover -s tests -v  28 passed
docker compose config --quiet            passed
```
