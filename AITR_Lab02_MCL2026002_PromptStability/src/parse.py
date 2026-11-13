"""Output parsers (protocol v1, section 1: scorer S1).

PubMedQA: strict JSON -> regex on the "decision" field -> invalid.
GSM8K: number after the last "The answer is" -> invalid.
"""
import json
import re

DECISIONS = ("yes", "no", "maybe")
CERTAINTIES = ("high", "moderate", "low")
_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.S | re.I)
_DECISION = re.compile(r'"decision"\s*:\s*"(yes|no|maybe)"', re.I)
_CONCLUSION = re.compile(r'"conclusion"\s*:\s*"((?:[^"\\]|\\.)*)"', re.S)
_CERTAINTY = re.compile(r'"certainty"\s*:\s*"(high|moderate|low)"', re.I)
_ANSWER = re.compile(r"the answer is\s*:?\s*\$?\s*(-?[\d,]*\.?\d+)", re.I)


def _clean(value, allowed):
    if not isinstance(value, str):
        return None
    v = value.strip().strip(".").strip().lower()
    return v if v in allowed else None


def parse_decision(raw: str) -> dict:
    """Return {decision, conclusion, certainty, parse_status}.

    decision is "yes" | "no" | "maybe" | "invalid"; parse_status is "json" | "regex" | "invalid".
    """
    text = raw.strip()
    m = _FENCE.match(text)
    if m:                      # deviation (logged): strip ``` fences before the strict parse
        text = m.group(1)
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            dec = _clean(obj.get("decision"), DECISIONS)
            if dec:
                concl = obj.get("conclusion")
                return {"decision": dec, "conclusion": concl if isinstance(concl, str) else None,
                        "certainty": _clean(obj.get("certainty"), CERTAINTIES), "parse_status": "json"}
    except json.JSONDecodeError:
        pass
    m = _DECISION.search(raw)
    if m:
        c = _CONCLUSION.search(raw)
        k = _CERTAINTY.search(raw)
        return {"decision": m.group(1).lower(), "conclusion": c.group(1) if c else None,
                "certainty": k.group(1).lower() if k else None, "parse_status": "regex"}
    return {"decision": "invalid", "conclusion": None, "certainty": None, "parse_status": "invalid"}


def parse_gsm8k(raw: str):
    """Final number after the last "The answer is", as a normalised string, or None."""
    hits = _ANSWER.findall(raw)
    if not hits:
        return None
    return normalise_number(hits[-1])


def normalise_number(s: str):
    s = s.replace(",", "").strip()
    try:
        x = float(s)
    except ValueError:
        return None
    return str(int(x)) if x == int(x) else repr(x)
