# Project continuity

For a new session or model handoff, read NewContext.md fully (the authoritative project specification), then docs/HANDOFF.md and docs/PROGRESS.md before continuing implementation. Read relevant supporting docs and inspect actual code for the task. Do not rename or duplicate NewContext.md.

Follow the user's phase approvals. A proposal is not approval; record new approvals in docs/HANDOFF.md and docs/PROGRESS.md. Latest explicit user instructions take precedence over older handoff notes.

Before a handoff or at the end of a work session, update docs/HANDOFF.md with completed work, any in-progress edits, latest test results, blockers, approval state and the exact next action. Update affected progress, decisions and source records too. Never put secrets in these files.

Treat documentation as a checkpoint, not proof that processes are still running or files are unchanged. Inspect Git status and relevant implementation before editing. Preserve existing work and raw data caches. Use README.md for local setup and verification commands.

Read docs/CURRENT_STATE.md fully with HANDOFF and PROGRESS. It records reconciled implementation and gaps. NewContext is requirements, not completion evidence; PRODUCT positioning and archived Done tables are not proof of implementation or approval. Latest user instructions override older plans. Distinguish source present, tests passed, built artifact, running server and physical-device acceptance. Never repeat old test counts as fresh results or invent API/integration availability. Update current sections in place and archive superseded facts. Preserve untracked work/runtime data; do not claim commit/backup unless created.
