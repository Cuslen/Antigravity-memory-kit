# 2026-10-12: Coding preferences

## Fact
- Before every change to a script, a backup copy is made (`Backups\<name>_<date>_<time>.py`).
- Minimal diffs: only change the lines that really need it.
- Scripts that run fine in practice are not refactored ("never touch a running system").

## Why
A "cleanup" once removed a fallback that turned out to be needed, and the script broke silently.

## How to apply
Propose changes as small diffs, mention the backup, and never remove existing fallbacks or defensive checks without asking.

Keywords: backup, refactor, diff, fallback, script
