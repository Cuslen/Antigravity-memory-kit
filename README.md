# Antigravity Memory Kit

A small, file-based long-term memory for **Gemini in Google Antigravity** – plus a hook that reminds Gemini
to actually use it.

Antigravity has no built-in memory across conversations, and it compacts long chats automatically, without
warning. Everything that only lived in the conversation is then reduced to a summary. This kit gives Gemini:

1. **A memory folder** – one Markdown file per topic and an `INDEX.md` with one line per memory.
2. **Rules in `GEMINI.md`** – when to read, when to write, what to save before and after a compaction.
3. **The Souffleur** – a `PreInvocation` hook that puts the matching memory in front of Gemini *before* she
   answers. This is the important part: in practice a model with a memory folder still answers "from memory"
   most of the time. In one setup, correction memories (hardware, car, health) were opened **zero times in
   150 messages**, and Gemini confidently named the wrong graphics card. With the Souffleur she reads the file.
4. **`read_transcript.py`** – lets Gemini look things up in her own transcript after a compaction
   (search, last steps, sent images) without Python one-liners that need confirmation.

Everything is plain files on your disk. You can read and fix every memory yourself.

Example – you write *"Which model fits on my graphics card?"*, and before answering Gemini sees:

```
Souffleur (automatic, not written by the user) - matching the user's message:
- hardware.md (PC hardware): Ryzen 7 7700, 32 GB RAM, RTX 4070 12 GB (never 64 GB, never a 3070!).
Read these files before you rely on the topic - they are newer than your memory.
Technical topic: check concrete facts (hardware, models, ports, versions) in your knowledge file before answering, not from memory.
```

## Files

| Path | What it is |
|---|---|
| `GEMINI.memory.md` | Memory and compaction rules to copy into your `~/.gemini/GEMINI.md` |
| `hooks/souffleur.py` | The PreInvocation hook |
| `hooks/souffleur_keywords.json` | Keyword → memory file mapping (example, edit it) |
| `hooks/hooks.json` | Hook registration (example) |
| `hooks/read_transcript.py` | Read-only transcript search |
| `example/Memories/` | An example `INDEX.md` and three memory files to show the format |

## Setup

1. **Memory folder** – create a folder for the memories, e.g. `C:\Gemini Workspace\Memories`, and start
   with an empty `INDEX.md` (or copy the examples to see how it works).
2. **Rules** – copy the content of `GEMINI.memory.md` into your `~/.gemini/GEMINI.md` and replace the
   placeholders (`<USER>`, `<MEMORY_DIR>`, `<KNOWLEDGE>`, `<HOOK_DIR>`).
3. **Hook files** – copy `souffleur.py`, `souffleur_keywords.json` and `read_transcript.py` into the folder
   where Antigravity looks for `hooks.json`. In Antigravity 2.0 on Windows this is `~/.gemini/config/`;
   the hook command runs with that folder as working directory.
4. **Configure** – set `MEMORY_DIR` at the top of `souffleur.py` and edit `souffleur_keywords.json`
   to match your memory files.
5. **Register** – add the `PreInvocation` entry from `hooks/hooks.json` to your `hooks.json`
   (or use the file as it is if you have none yet).
6. **Restart Antigravity** so it reads `hooks.json` again.

Test it by asking something that matches a keyword. `souffleur.log` (next to the script) shows whether the
hook ran and what it matched – it never stores the text of your messages.

## How the Souffleur decides

- A memory matches when your message contains one of its keywords from `souffleur_keywords.json`,
  a word (5+ letters) from its title in `INDEX.md`, or a word from the `Keywords:` line at the end of
  the memory file. Gemini writes that line herself when she creates a memory (rule in `GEMINI.memory.md`),
  so new memories are hooked up right away without touching the keyword list.
- From the `Keywords:` line at most 12 words count, and everyday words (`STOPWORDS` in `souffleur.py`,
  e.g. "make", "get") are dropped – add your own if a word fires too often.
- Words shorter than 5 characters must match as a whole word (`ram` doesn't fire on `program`),
  longer ones also as word start (`compact` fires on `compaction`).
- At most 4 memories per note, best matches first. `_knowledge` words add an extra hint
  (`_knowledge_hint`), e.g. "check your setup file before stating hardware facts".
- The note is injected **once per user message** as an *ephemeral* message: Gemini sees it for that answer,
  it is dropped afterwards and doesn't pile up in the context.
- Keep the keywords specific. If every message triggers a note, the model learns to ignore it.

## About Antigravity hooks

Antigravity supports hooks, but at the time of writing they are not documented on the web. The
documentation ships inside the Antigravity installation (`resources/bin/language_server.exe` contains a
"Hook Spec Fields" section). The parts this kit relies on:

- Events: `SessionStart`, `PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation`, `Stop`.
- **Only `PreToolUse` and `PostToolUse` use the `matcher` + `hooks` wrapper.** All other events take a
  **flat list** of handlers. A `PreInvocation` entry wrapped like a `PreToolUse` entry is silently ignored.
- `PreInvocation` receives JSON on stdin with `invocationNum`, `initialNumSteps` and common fields such as
  `conversationId`, `lastUserInput` and `transcriptPath`.
- It may answer with
  ```json
  {"injectSteps": [{"ephemeralMessage": "text"}]}
  ```
  Other step types: `{"userMessage": "text"}` and `{"systemMessage": {"systemMessage": "text", "metadata": {}}}`
  (the latter persists in the conversation).
- `PreToolUse` answers with `decision`: `allow`, `deny`, `ask` or `force_ask` (asks even with "Always allow").

## Caveats

- Built on **undocumented** behaviour (hook events, transcript format). An Antigravity update can break it.
- Tested on Windows 11 with Antigravity 2.0 (up to v2.28.2) only.
- The keyword matching is simple on purpose. It won't catch everything – add words when you notice a miss.
- Not affiliated with Google. "Gemini" and "Antigravity" are trademarks of Google.

## Changelog

- **1.0.1** – Memories can carry their own triggers: a `Keywords:` line at the end of a memory file is read
  by the Souffleur (with a stopword filter and a cap of 12 words). New GEMINI.md rule so Gemini adds the line
  whenever she creates a memory. Examples updated.
- **1.0.0** – First release.

## Related

[Gemini-Tacho](https://github.com/Cuslen/Gemini-Tacho) – shows how full the Antigravity context is, so you
know when a compaction is coming.
