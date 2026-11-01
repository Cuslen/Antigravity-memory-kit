r"""Souffleur - a PreInvocation hook for Google Antigravity.

Runs before every model call. Reads the user's last message, finds matching
memory files (keyword list souffleur_keywords.json, title words from the
memory INDEX.md and a "Keywords:" line inside each memory) and injects a short, ephemeral note into Gemini's context -
once per user message: which file, the one-line summary from the INDEX and,
for technical topics, an optional hint where to look things up.

Why: a model with a memory folder still answers "from memory" most of the time
instead of opening the right file. Measured in one setup: in 150 user messages,
correction memories (hardware, car, health) were opened zero times, and the
model confidently stated the wrong graphics card. The note puts the right file
in front of it at the right moment.

Defensive by design: any error -> empty output, Gemini works on normally.
souffleur.log only stores field names, lengths and hits - never message text.
"""
import hashlib
import json
import os
import re
import sys
import time

# --- configure ---------------------------------------------------------------
# Folder with your memory files and INDEX.md (one line per memory:
# "- Title | file.md | one-line summary").
MEMORY_DIR = os.path.join(os.path.expanduser("~"), "Gemini Workspace", "Memories")
MAX_HITS = 4
# Title words that are too generic to trigger a memory on their own
GENERIC = {"notes", "setup", "status", "memory", "memories", "workflow", "project",
           "projects", "general", "update", "about"}
# A memory file may end with a line "Keywords: word1, word2, ..." - the model
# maintains it itself when it creates the memory. Everyday words are dropped,
# otherwise e.g. "make" would fire on every second message.
MAX_FILE_KEYWORDS = 12
STOPWORDS = {"make", "makes", "making", "get", "gets", "getting", "go", "going", "do", "doing",
             "have", "thing", "things", "today", "tomorrow", "always", "never", "good", "new",
             "file", "files", "question", "thanks", "please", "user", "gemini"}
# -----------------------------------------------------------------------------
KEYWORD_LINE = re.compile(r"^\W*keywords?\W*:\s*(.+)$", re.IGNORECASE)

HERE = os.path.dirname(os.path.abspath(__file__))
KEYWORDS = os.path.join(HERE, "souffleur_keywords.json")
STATE = os.path.join(HERE, "souffleur_state.txt")
LOG = os.path.join(HERE, "souffleur.log")
INDEX = os.path.join(MEMORY_DIR, "INDEX.md")


def log(line):
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) > 200_000:
            os.replace(LOG, LOG + ".old")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + line + "\n")
    except OSError:
        pass


def fields(obj, path=""):
    """Field names and types (no content) - for the log."""
    if isinstance(obj, dict):
        out = []
        for k, v in obj.items():
            out += fields(v, f"{path}.{k}" if path else k)
        return out
    if isinstance(obj, list):
        return [f"{path}[{len(obj)}]"]
    if isinstance(obj, str):
        return [f"{path}:str{len(obj)}"]
    if isinstance(obj, (int, float, bool)):
        return [f"{path}:{type(obj).__name__}={obj}"]
    return [f"{path}:{type(obj).__name__}"]


def find_field(obj, names):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in names and isinstance(v, (str, int)):
                return v
        for v in obj.values():
            r = find_field(v, names)
            if r is not None:
                return r
    return None


def last_message(data):
    text = find_field(data, {"lastUserInput", "last_user_input"})
    if isinstance(text, str) and text.strip():
        return text, "field"
    path = find_field(data, {"transcriptPath", "transcript_path"})
    if isinstance(path, str) and os.path.isfile(path):
        last = None
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"USER_INPUT"' in line:
                    last = line
        if last:
            try:
                return str(json.loads(last).get("content") or ""), "transcript"
            except ValueError:
                pass
    return "", "none"


def index_entries():
    """Lines '- Title | file.md | summary' -> {file: (title, summary)}."""
    entries = {}
    try:
        with open(INDEX, encoding="utf-8", errors="replace") as f:
            for line in f:
                parts = [p.strip() for p in line.lstrip("- ").split("|")]
                if len(parts) >= 3 and parts[1].endswith(".md"):
                    entries[parts[1]] = (parts[0], parts[2])
    except OSError:
        pass
    return entries


def file_keywords(file):
    """Last 'Keywords:' line of a memory file, filtered and capped."""
    if os.path.basename(file) != file:  # only files directly in MEMORY_DIR
        return []
    line = None
    try:
        with open(os.path.join(MEMORY_DIR, file), encoding="utf-8", errors="replace") as f:
            for l in f:
                m = KEYWORD_LINE.match(l.strip())
                if m:
                    line = m.group(1)
    except OSError:
        return []
    if not line:
        return []
    words = []
    for w in line.replace(";", ",").split(","):
        w = w.strip(" *`\"'.").lower()
        if len(w) >= 3 and w not in STOPWORDS and w not in words:
            words.append(w)
    return words[:MAX_FILE_KEYWORDS]


def matches(text, word):
    w = re.escape(word.lower())
    if len(word) < 5:
        return re.search(rf"(?<!\w){w}(?!\w)", text) is not None
    return re.search(rf"(?<!\w){w}", text) is not None


def hits(text, keywords, index):
    t = text.lower()
    found = []
    for file, (title, _) in index.items():
        words = list(keywords.get(file, [])) + file_keywords(file)
        words += [w for w in re.findall(r"[^\W_]{5,}", title.lower()) if w not in GENERIC]
        n = sum(1 for w in set(words) if matches(t, w))
        if n:
            found.append((n, file))
    found.sort(key=lambda x: -x[0])
    knowledge = any(matches(t, w) for w in keywords.get("_knowledge", []))
    return [f for _, f in found[:MAX_HITS]], knowledge


def note(files, knowledge, index, keywords):
    lines = ["Souffleur (automatic, not written by the user) - matching the user's message:"]
    for f in files:
        title, summary = index[f]
        lines.append(f"- {f} ({title}): {summary}")
    if files:
        lines.append("Read these files before you rely on the topic - they are newer than your memory.")
    if knowledge and keywords.get("_knowledge_hint"):
        lines.append(keywords["_knowledge_hint"])
    return "\n".join(lines)


def main():
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")  # Windows console would be cp1252
    data = json.loads(raw) if raw.strip() else {}
    text, source = last_message(data)
    nr = find_field(data, {"invocationNum", "invocation_num"})
    key = hashlib.sha256((str(find_field(data, {"conversationId", "conversation_id"})) + text).encode()).hexdigest()
    try:
        done = open(STATE, encoding="utf-8").read().strip() == key
    except OSError:
        done = False
    if not text or done:
        log(f"skip source={source} nr={nr} done={done} fields={fields(data)[:40]}")
        sys.stdout.write("{}")
        return
    with open(STATE, "w", encoding="utf-8") as f:
        f.write(key)
    keywords = json.load(open(KEYWORDS, encoding="utf-8"))
    index = index_entries()
    files, knowledge = hits(text, keywords, index)
    log(f"new source={source} nr={nr} length={len(text)} hits={files} knowledge={knowledge} "
        f"fields={fields(data)[:40]}")
    if not files and not (knowledge and keywords.get("_knowledge_hint")):
        sys.stdout.write("{}")
        return
    sys.stdout.write(json.dumps({"injectSteps": [{"ephemeralMessage": note(files, knowledge, index, keywords)}]},
                                ensure_ascii=True))  # \u escapes: independent of the console code page


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never block Gemini's answer
        log(f"ERROR {type(e).__name__}: {e}")
        sys.stdout.write("{}")
