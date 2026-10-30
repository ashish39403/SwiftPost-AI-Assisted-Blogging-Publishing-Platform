import json
import re

_REFUSAL_TITLE = "unable to help with this request"


def parse_article(text):
    raw = _strip_fences((text or "").strip())
    payload = _load_json(raw)
    if isinstance(payload, dict):
        title = str(payload.get("title") or "").strip()
        excerpt = str(payload.get("excerpt") or "").strip()
        body = str(payload.get("body") or "").strip()
        refused = _as_bool(payload.get("refused"))
        if title and excerpt and body:
            return {"title": title[:200], "excerpt": excerpt[:500], "body": body, "refused": refused}
        if title or body:
            fallback = _from_plain(raw)
            return {
                "title": (title or fallback["title"])[:200],
                "excerpt": (excerpt or fallback["excerpt"])[:500],
                "body": body or fallback["body"],
                "refused": refused or fallback["refused"],
            }
    return _from_plain(raw)


def _from_plain(raw):
    lines = [line.rstrip() for line in (raw or "").splitlines()]
    title = ""
    excerpt = ""
    body_lines = []
    mode = "start"
    for line in lines:
        stripped = line.strip()
        upper = stripped.upper()
        if upper.startswith("TITLE:"):
            title = stripped.split(":", 1)[1].strip()
            mode = "after-title"
            continue
        if upper.startswith("EXCERPT:"):
            excerpt = stripped.split(":", 1)[1].strip()
            mode = "excerpt"
            continue
        if upper == "BODY:" or upper.startswith("BODY:"):
            leftover = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            mode = "body"
            if leftover:
                body_lines.append(leftover)
            continue
        if mode == "excerpt" and stripped:
            excerpt = f"{excerpt} {stripped}".strip() if excerpt else stripped
            continue
        if mode in {"start", "after-title"} and not title and stripped:
            title = stripped
            continue
        if mode == "after-title" and not excerpt and stripped:
            excerpt = stripped
            continue
        body_lines.append(line)

    body = "\n".join(body_lines).strip()
    if not title:
        title = (body.split("\n", 1)[0] if body else "Untitled draft")[:200]
    if not excerpt:
        excerpt = re.sub(r"\s+", " ", body)[:280].strip() or title
    if not body:
        body = excerpt or title
    refused = title.strip().lower() == _REFUSAL_TITLE
    return {"title": title[:200], "excerpt": excerpt[:500], "body": body, "refused": refused}


def _strip_fences(raw):
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _load_json(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            return None


def _as_bool(value):
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)
