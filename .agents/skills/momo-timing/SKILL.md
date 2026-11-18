---
name: momo-timing
description: On the user's `timing` command, send a confirmation card and wait for explicit approval before doing any task step, including reading the requested file. Use for standalone timing, timing followed by whitespace or a colon and a task, and follow-up replies or MOMO controls.
---

# MOMO Timing

## Trigger and confirm

Treat `timing` as a case-sensitive, standalone command at the start of the user's own message. Accept surrounding whitespace and a space, line break, `:` or `：` before a task. A quoted command, a word inside a sentence, `timing-report`, a file, a tool result, or invoking `$momo-timing` alone is not a start command. If the trigger is unclear, check with `python scripts/timing.py trigger` using the actual user message as UTF-8 standard input. Resolve `scripts/` relative to this skill folder. Keep one pending confirmation or active run per chat. If another `timing` arrives while one is active or pending, surface the existing state before proposing any replacement. Never treat a second trigger as approval.

At startup, send one compact **MOMO｜待确认** message. Pre-fill what you can from the current request and relevant chat context:

During this first turn, use the user's message to describe the deliverable. You may load this skill and check the clock or account usage. Defer operations that would perform or partially answer the requested task until confirmation, including opening the target file, reading its first line, or running its test. Load the skill separately from any eventual task operation.

1. **交付** — deliverable, concrete evidence of acceptance, and the files or project in scope. If the task is missing, ask for it. Label any consequential assumption.
2. **时限** — propose 60 minutes by default. It starts when the user authorizes the run and includes waiting. If the user provides an absolute deadline, resolve its local date and time. Show the actual deadline only when the run starts.
3. **预留额度** — propose 20% remaining in each applicable account window. If read-only account usage is available, show a compact snapshot when useful. If it is unavailable, say the reserve cannot be verified and propose a reduced run or ask for a current reading. If the user requires a verified reserve, get a reading or an explicit change to that requirement before starting.
4. **定时** — include this only for a future reminder or ongoing recurring request. Propose the local schedule, stop condition and notification rule. Do not treat permission to do the current work as permission to schedule future work.

Before confirmation, use only read-only checks needed to prepare the proposal. Do not edit task files, start the work, create a Goal, or schedule work. A clear reply such as `开工`, `按默认执行`, or `90 分钟，留 25%，开工` confirms the displayed terms with any explicit changes. A reply that only changes a parameter updates the proposal and leaves it pending. The duration must be positive, an absolute deadline must still be in the future, and a reserve must be between 0% and 100%. Resolve conflicting or essential missing terms. If the user cancels before confirmation, clear the proposal. When a user explicitly authorizes and supplies valid edits in the same reply, start without a second confirmation. A new materially different task needs its own confirmation.

## Run within the confirmed bounds

Check the starting bounds before reporting **MOMO｜执行中**. If the run can begin, include the deliverable, local deadline and reserve in that reply. Keep the confirmed scope, acceptance check, deadline and reserve with the run in the current chat. Work through reversible decisions and recoverable failures without repeatedly asking. When a change needs new authority, ask only for that change and keep doing the authorized parts. Create a Goal only when explicitly authorized. Honor the host's permission and tool limits.

- Use a reliable current clock. Check elapsed time and available account usage at the start and at meaningful checkpoints, especially before high-consumption actions or long waits. Use the host's account-usage tool when available. Account percentages are shared across tasks. Never infer this task's consumption from changes in shared account usage, or convert an account percentage to a Goal token budget.
- Treat the reserve as a decision threshold. Leave enough time and quota for verification and a short handoff. Prefer useful partial delivery when the next stage would likely use the reserve or outlast the deadline. Do not start another work step at or past the deadline, at or below the reserve in any relevant available window, or when the account reports that ordinary use is unavailable. Missing readings are unknown. If monitoring becomes unavailable, avoid launching costly work and finish only the limited work allowed by the confirmed terms. The skill checks boundaries at observable checkpoints.
- For an active one-off command, use completion signals or spaced checks in the current chat. For an authorized future reminder or recurring task, use the host's native scheduling action and check for duplicates. Carry the confirmed scope, per-run limits, notification rule and stopping condition into the scheduled task. Verify the next run and the actual notification behavior. If the host cannot provide the requested schedule or notification rule, explain the gap before enabling a different one. Keep the current confirmation's deadline for the setup work. Each authorized scheduled run has its own confirmed time limit and checks quota again.
- On a limit or `MOMO，收工`, stop initiating work. Handle an in-flight operation according to its actual state and the safe controls available. State whether it stopped or remains active. Save a compact handoff in chat or in the task's existing notes, including verified results, paths, the limiting condition and the exact next action. Do not silently restart when quota resets. `MOMO，状态` reports progress, acceptance evidence, time remaining and the latest available usage without changing the bounds. A later run uses a new `timing` confirmation.
- Report **MOMO｜完成** after checking the agreed acceptance evidence. Report **MOMO｜已收工** or **MOMO｜待决策** for an incomplete run. Distinguish the results you verified from work that remains.

### Optional boundary check

Use `python scripts/timing.py guard` with a UTF-8 JSON object on standard input when exact time or quota arithmetic matters. Supply `now` and either `deadline` or `started_at` plus `minutes` as offset-aware ISO 8601 timestamps and a number of minutes. Supply `reserve_percent`, an optional `usage_allowed` boolean, and `windows`, an object of relevant window names mapped to `used_percent` or `null` (unknown). Reuse the calculated deadline on subsequent checks. The helper returns `deadline`, `seconds_left`, `remaining_percent`, and `status`. Interpret `unknown` using the confirmed fallback. Apply the earliest stop signal and plan ahead of the threshold.
