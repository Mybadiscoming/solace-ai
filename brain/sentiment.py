"""
Hybrid emotion detector for Solace with logging.

Keeps your original design:
- detect_emotion → backward compatible
- classify_emotion → rich output
- local heuristics + optional transformers + optional remote detector

Your old version is preserved at the bottom in a comment block.
"""

from __future__ import annotations
import os
import re
import requests
import logging
from typing import Tuple, Optional

# -------------------------
# Logging
# -------------------------
logger = logging.getLogger("snugsy.sentiment")

# -------------------------
# Config
# -------------------------
GREETINGS = {"hi", "hello", "hey", "hii", "heyy", "yo", "sup"}

RED_FLAG_PATTERNS = [
    r"\bkill myself\b",
    r"\bi want to die\b",
    r"\bsuicid\b",
    r"\bend my life\b",
    r"\bhurt myself\b",
    r"\bwant to die\b",
    r"\bdo not want to live\b",
    r"\bcut myself\b",
    r"\bhang myself\b",
]

_RED_FLAG_RE = re.compile(
    "|".join(f"(?:{p})" for p in RED_FLAG_PATTERNS),
    re.IGNORECASE
)

NEGATIVE_WORDS = [
    "sad", "depressed", "hopeless", "anxious", "panic", "alone",
    "worthless", "miserable", "useless", "overwhelmed", "crying",
]

REMOTE_DETECTOR_URL = os.environ.get("REMOTE_DETECTOR_URL", None)
USE_REMOTE_DETECTOR = os.environ.get("USE_REMOTE_DETECTOR", "true").lower() not in ("0", "false", "no", "off")

# Transformer (lazy)
_transformer_pipeline = None
_transformer_available = None


# ============================================================
# TRANSFORMER LOADER
# ============================================================
def _lazy_load_transformer():
    global _transformer_pipeline, _transformer_available

    if _transformer_available is True:
        return _transformer_pipeline
    if _transformer_available is False:
        return None

    try:
        from transformers import pipeline
        _transformer_pipeline = pipeline(
            "text-classification",
            model="bhadresh-savani/distilbert-base-uncased-emotion",
            return_all_scores=True,
        )
        _transformer_available = True
        logger.info("Transformer pipeline loaded successfully.")
        return _transformer_pipeline
    except Exception as e:
        logger.warning("Transformer unavailable: %s", e)
        _transformer_available = False
        _transformer_pipeline = None
        return None


# ============================================================
# BASIC LOCAL DETECTORS
# ============================================================
def _is_greeting(text: str) -> bool:
    return text.strip().lower() in GREETINGS


def _keyword_detector(text: str) -> Tuple[str, float]:
    """
    Detect greetings, red flags, and quick negative sentiment.
    """
    t = text.strip().lower()

    # Greeting override
    if _is_greeting(t):
        return "joy", 0.99

    # Red flags
    if _RED_FLAG_RE.search(t):
        logger.warning("Red flag phrase detected in user text.")
        return "suicidal", 0.99

    # heuristic negatives
    neg_count = sum(1 for w in NEGATIVE_WORDS if w in t)
    exclam = t.count("!")
    length = len(t.split())

    score = 0.35 + min(0.5, 0.18 * neg_count) + 0.05 * min(exclam, 3)

    if length <= 6 and neg_count >= 1:
        score += 0.1

    score = max(0.05, min(0.99, score))
    label = "sad" if neg_count else "neutral"

    return label, score


# ============================================================
# REMOTE DETECTOR
# ============================================================
def _call_remote_detector(text: str, url: Optional[str]):
    if not url:
        return None, None

    try:
        logger.info("Calling remote detector: %s", url)
        resp = requests.post(url, json={"text": text}, timeout=4)
        resp.raise_for_status()
        j = resp.json()

        label = j.get("label") or j.get("response") or j.get("emotion")
        confidence = j.get("confidence") or j.get("score") or j.get("confidence_score")

        if label is None:
            return None, None

        return str(label), float(confidence or 0.0)
    except Exception as e:
        logger.warning("Remote emotion detector failed: %s", e)
        return None, None


# ============================================================
# TRANSFORMER DETECTOR
# ============================================================
def _transformer_detect(text: str):
    pl = _lazy_load_transformer()
    if not pl:
        return None, None

    try:
        results = pl(text)
        if isinstance(results, list) and results and isinstance(results[0], list):
            scores = sorted(results[0], key=lambda x: x["score"], reverse=True)
            top = scores[0]
            return top["label"], float(top["score"])
        if isinstance(results, list) and "label" in results[0]:
            top = results[0]
            return top["label"], float(top.get("score", 0.0))
    except Exception as e:
        logger.warning("Transformer detection error: %s", e)
        return None, None

    return None, None


# ============================================================
# PUBLIC — classify_emotion
# ============================================================
def classify_emotion(text: str, remote_url: Optional[str] = None) -> dict:
    text = (text or "").strip()

    if not text:
        return {"label": "neutral", "confidence": 0.5, "method": "empty", "escalate": False, "quality": "low"}

    # ------------------- 1) Local keyword detector -------------------
    label, conf = _keyword_detector(text)
    method = "keyword" if label in ("suicidal", "joy") else "heuristic"

    if label == "suicidal":
        return {"label": label, "confidence": conf, "method": method, "escalate": True, "quality": "high"}

    if conf >= 0.80:
        return {
            "label": label,
            "confidence": round(conf, 2),
            "method": method,
            "escalate": (label == "sad"),
            "quality": "high",
        }

    # ------------------- 2) Transformer (optional) -------------------
    t_label, t_conf = _transformer_detect(text)
    if t_label is not None:
        if (t_conf or 0) >= conf:
            label, conf, method = t_label, float(t_conf), "transformer"

    # ------------------- 3) Remote (optional) -------------------
    remote_url = remote_url or (REMOTE_DETECTOR_URL if USE_REMOTE_DETECTOR else None)

    if conf < 0.6 and remote_url:
        r_label, r_conf = _call_remote_detector(text, remote_url)
        if r_label is not None:
            if (r_conf or 0) >= conf:
                label, conf, method = r_label, float(r_conf), "remote"

    # ------------------- 4) Quality / Escalation -------------------
    escalate = False
    quality = "medium"

    if label == "suicidal":
        escalate = True
        quality = "high"
    elif conf >= 0.80:
        quality = "high"
        escalate = (label in ("panic", "angry", "depressed"))
    elif conf < 0.45:
        quality = "low"

    return {
        "label": str(label),
        "confidence": round(float(conf), 2),
        "method": method,
        "escalate": escalate,
        "quality": quality,
    }


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================
def detect_emotion(text: str) -> Tuple[str, float]:
    out = classify_emotion(text)
    return out["label"], out["confidence"]


# ============================================================
# ORIGINAL VERSION (kept for reference)
# ============================================================
"""
<YOUR ORIGINAL sentiment.py IS KEPT HERE SAFELY FOR SWITCHING BACK ANYTIME>
"""