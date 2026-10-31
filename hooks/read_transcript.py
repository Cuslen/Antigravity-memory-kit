r"""Read Gemini's own Antigravity transcript - read only, text only.

Built so Gemini can look things up after a compaction without writing her own
Python one-liners (which need confirmation) or dumping whole JSON lines into
her context with Select-String / grep.

Usage:
  python read_transcript.py search "<pattern>" [--max 10] [--chat <id-start>] [--full]
  python read_transcript.py steps <from> <to>  [--chat <id-start>] [--full]
  python read_transcript.py last [count]       [--chat <id-start>] [--full]
  python read_transcript.py images [count]     [--chat <id-start>] [--full]

  search  Regular expression (case-insensitive) in the text of the steps; shows
          each hit with +-300 characters around it.
  steps   Shows steps from..to (at most 1500 characters each, max. 40 steps).
  last    Shows the last steps with text (default 10, max. 40) - after a
          compaction, when the step numbers are unknown.
  images  Lists the images the user sent, with step and path (default 10,
          max. 50); open them with view_file.
  --chat  Start of the chat ID; default is the most recently active chat.
  --full  transcript_full.jsonl instead of transcript.jsonl.

Reads only files below ~/.gemini/antigravity/brain/. No file path as
argument, no write access.
"""
import argparse
import glob
import json
import os
import re
import sys

BRAIN = os.path.join(os.path.expanduser("~"), ".gemini", "antigravity", "brain")
CONTEXT = 300
STEP_MAX = 1500


def transcript(chat, full):
    name = "transcript_full.jsonl" if full else "transcript.jsonl"
    pattern = os.path.join(BRAIN, (chat or "") + "*", ".system_generated", "logs", name)
    files = glob.glob(pattern)
    if not files:
        sys.exit(f"No transcript found ({'chat ' + chat if chat else 'no chat'}).")
    return max(files, key=os.path.getmtime)


def entries(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if isinstance(o, dict):
                yield o


def text_of(o):
    parts = []
    if isinstance(o.get("content"), str) and o["content"].strip():
        parts.append(o["content"])
    calls = o.get("tool_calls")
    if isinstance(calls, list) and calls:
        names = [str(c.get("name")) for c in calls if isinstance(c, dict)]
        parts.append("[tools: " + ", ".join(names) + "]")
    for m in images_of(o):
        parts.append("[image: " + m + "]")
    return "\n".join(parts)


def images_of(o):
    media = o.get("media")
    if not isinstance(media, list):
        return []
    return [os.path.normpath(str(m.get("uri"))) for m in media
            if isinstance(m, dict) and m.get("uri")]


def header(o):
    return (f"=== #{o.get('step_index')} {o.get('type', '')}/{o.get('source', '')} "
            f"{str(o.get('created_at', ''))[:19]} ===")


def search(path, pattern, maximum):
    try:
        rx = re.compile(pattern, re.I)
    except re.error:
        rx = re.compile(re.escape(pattern), re.I)
    n = 0
    for o in entries(path):
        t = text_of(o)
        m = rx.search(t)
        if not m:
            continue
        a, e = max(0, m.start() - CONTEXT), min(len(t), m.end() + CONTEXT)
        print(header(o))
        print(("…" if a else "") + t[a:e] + ("…" if e < len(t) else ""))
        n += 1
        if n >= maximum:
            print(f"(stopped after {maximum} hits - use --max for more)")
            break
    if n == 0:
        print("No hits.")


def steps(path, start, end):
    n = 0
    for o in entries(path):
        s = o.get("step_index")
        if isinstance(s, int) and start <= s <= end:
            t = text_of(o)
            if not t:
                continue
            print(header(o))
            print(t[:STEP_MAX] + ("…" if len(t) > STEP_MAX else ""))
            n += 1
    if n == 0:
        print("No steps with text in this range.")


def last(path, count):
    with_text = [o for o in entries(path) if text_of(o)]
    for o in with_text[-count:]:
        t = text_of(o)
        print(header(o))
        print(t[:STEP_MAX] + ("…" if len(t) > STEP_MAX else ""))
    if not with_text:
        print("No steps with text.")


def images(path, count):
    found = [(o, b) for o in entries(path) for b in images_of(o)]
    for o, b in found[-count:]:
        print(f"#{o.get('step_index')} {str(o.get('created_at', ''))[:19]}  {b}")
    if not found:
        print("No images in the transcript.")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description="Read the Antigravity transcript (read only)")
    sub = p.add_subparsers(dest="mode", required=True)
    s1 = sub.add_parser("search")
    s1.add_argument("pattern")
    s1.add_argument("--max", type=int, default=10)
    s2 = sub.add_parser("steps")
    s2.add_argument("start", type=int)
    s2.add_argument("end", type=int)
    s3 = sub.add_parser("last")
    s3.add_argument("count", type=int, nargs="?", default=10)
    s4 = sub.add_parser("images")
    s4.add_argument("count", type=int, nargs="?", default=10)
    for s in (s1, s2, s3, s4):
        s.add_argument("--chat", default="")
        s.add_argument("--full", action="store_true")
    a = p.parse_args()
    if a.chat and not re.fullmatch(r"[0-9a-f-]{1,36}", a.chat):
        sys.exit("--chat expects the start of a chat ID (0-9, a-f).")
    path = transcript(a.chat, a.full)
    print(f"Transcript: {os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path))))[:8]}"
          f" ({os.path.basename(path)})")
    if a.mode == "search":
        search(path, a.pattern, max(1, min(a.max, 50)))
    elif a.mode == "last":
        last(path, max(1, min(a.count, 40)))
    elif a.mode == "images":
        images(path, max(1, min(a.count, 50)))
    else:
        steps(path, a.start, min(a.end, a.start + 40))


if __name__ == "__main__":
    main()
