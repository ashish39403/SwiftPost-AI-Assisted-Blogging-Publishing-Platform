import json
import re

from rest_framework.exceptions import ValidationError


def parse_article(text):
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    payload = _load_json(raw)
    if not isinstance(payload, dict):
        raise ValidationError({"output": "The writing model did not return usable article JSON."})
    title = str(payload.get("title") or "").strip()
    excerpt = str(payload.get("excerpt") or "").strip()
    body = str(payload.get("body") or "").strip()
    if not title or not excerpt or not body:
        raise ValidationError({"output": "The writing model omitted the title, excerpt, or body."})
    refused = payload.get("refused")
    if isinstance(refused, str):
        refused = refused.strip().lower() in {"true", "1", "yes"}
    else:
        refused = bool(refused)
    return {"title": title[:200], "excerpt": excerpt[:500], "body": body, "refused": refused}


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
