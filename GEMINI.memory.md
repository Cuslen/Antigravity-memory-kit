<!--
Memory section for your GEMINI.md (Antigravity reads ~/.gemini/GEMINI.md with every message).
Copy the part below into your own GEMINI.md and replace the placeholders:
  <USER>         your name, e.g. Alex
  <MEMORY_DIR>   folder with INDEX.md and the memory files, e.g. C:\Gemini Workspace\Memories
  <KNOWLEDGE>    optional: a file with your setup / technical facts (hardware, network, tools)
  <HOOK_DIR>     folder of read_transcript.py, e.g. C:\Users\<you>\.gemini\config
Delete the KNOWLEDGE lines if you don't keep such a file.
-->

# MEMORY
- At the start of every conversation you read only <MEMORY_DIR>\INDEX.md. It has one line per memory: title, file name, one-line summary. You read a memory file only when it fits the current topic.
- One memory = one file = one topic, e.g. coding-preferences.md. At the top the date, then the fact, then "Why" (the reason) and "How to apply" (what you do differently from now on).
- CHECKPOINT BEFORE EVERY ANSWER: Does <USER>'s message contain a decision, a preference, a correction of you or a milestone? Typical signals: "no", "that's wrong", "actually …", "from now on", "always", "never", "rather", "I want", "it worked", "done". If yes: create or update the memory in the same turn (without being asked), then answer and mention it briefly. Don't postpone it.
- If a memory contradicts another file, the memory wins – it is newer. So before personal or project-related statements, check INDEX.md for a memory on the topic and read it.
- What you remember: <USER>'s decisions and preferences, corrections of you ("that was wrong because …"), the state of running projects, things you should not ask again.
- What you don't remember: passwords, keys, account numbers; anything that already has its own file.
- Before creating a memory, check whether a matching one exists and update it instead of creating a duplicate. Wrong memories are corrected, not deleted.
- After every new or changed memory you update INDEX.md. Keep the index short, at most one line per entry.
- Rather one memory too many than one too few – disk space doesn't matter, what isn't in a file is lost at the next compaction.
- If a note starting with "Souffleur (automatic, not written by the user)" appears before your answer, read the files it names before you rely on the topic.
- Knowledge: <KNOWLEDGE>. Before you state a concrete fact about <USER>'s setup (number, model, version, port, path), check it there by keyword search, even in a casual conversation. Never guess; if you find nothing, say so.

# COMPACTION
- Antigravity compacts automatically at roughly 243,000–265,000 tokens – without warning, even mid-conversation. So you save important things right away (checkpoint), not just before compaction.
- If <USER> says "prepare for compaction", you save everything that so far only exists in the conversation: decisions, preferences, corrections and project state as memories (update INDEX.md). Then report briefly what you saved.
- After a compaction you read INDEX.md again and don't continue with facts from the summary that you can't verify in the files.
- To look something up in your own transcript you use only the read script (runs without confirmation, shows text only, shortened):
  `python "<HOOK_DIR>\read_transcript.py" search "<pattern>"` – hits with context
  `python "<HOOK_DIR>\read_transcript.py" last [count]` – the last steps, when you don't know the step numbers
  `python "<HOOK_DIR>\read_transcript.py" steps <from> <to>` – a range of steps
  `python "<HOOK_DIR>\read_transcript.py" images [count]` – paths of images <USER> sent; open them with view_file
  No own Python one-liners or grep/Select-String on the JSONL files – they need confirmation or flood your context with whole JSON lines.
