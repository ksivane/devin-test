# Devin - Take Home Assignment
**Kailash P. Sivanesan**

## Deliverables
### Video to VP of Engineering and technical SMEs curious about Devin.

[Loom video](https://www.loom.com/share/f60de63084794a3b80ccd80b92c8b332)

### superset repo copy
[devin-superset](https://github.com/ksivane/devin-superset/tree/devin/1779280717-clean-config-updates)


## Assignment
You will build an event-driven automation using the Devin API that solves a concrete engineering workflow problem. You should present your solution as if pitching Devin to a VP of Engineering, alongside senior engineers who will evaluate your technical depth.

## Demo: Devin Secrets Remediator & PR Reviewer
This demo automates secrets remediation and leakage using Devin AI. It monitors a specified repository for PRs and triggers a Devin session. Devin takes autonomous actions to remediate any secrets leakage findings, performs a code review based on a structured prompt and schema, and displays the results (summary, actions, security findings) for auditability and observability.


## Instructions to Run Demo
1.  **Start Docker container**: `docker run ksivane/devin-test-kp:0.2`. Ensure it starts successfully without errors.
2.  **Fork the repository**: Fork [devin-superset](https://github.com/ksivane/devin-superset) into your own account.
3.  **Create a PR**: Create a branch, edit some code to create secrets leakage, and raise a PR to `ksivane/devin-superset` main.
4.  **Wait for processing**: The container should catch the new PR within 15 seconds and kick off Devin security remediation by connecting to app.Devin.ai.
5.  **Wait for results**: Depending on resource availability, Devin can take upto 3 mins to finish. You will see useful summary, info and technical summary at the end.

## Design choices / Assumptions
- **Session Management**: Uses the programmatic API to create, resume, and manage Devin sessions.
- **Session Continuity**: Existing sessions are resumed if possible; otherwise, a new session is created.
- **API Choice**: Uses the sessions API directly instead of "Devin Review".
- **Polling**: The demo polls for PRs every 15 seconds. Webhooks were avoided to simplify the demo setup by not requiring an internet-facing endpoint.
- **Output**: Shows useful Devin session output to the audience. Detailed logs for the session can be seen in `app.devin.ai` if needed.
- **Configuration**: One-time configuration of `app.devin.ai` was done (org_id, api_key, and secret store).
- **Processing**: One PR is processed per run in this demo.
- **Security**: All tokens and API keys used for this demo are ephemeral.
- **Audience**: Currently reviewing their enterprise cybersecurity controls due to recent incidents and would like to know what Devin can do for them.

## Repo copy with Devin remediations
[devin-superset](https://github.com/ksivane/devin-superset)

![Screenshot](./devin-Screenshot%202026-05-21%20135240.png)

