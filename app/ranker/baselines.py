from __future__ import annotations
from typing import List, Dict, Any, Tuple
import re

from app.db.repo import list_recipes

WORD_RE = re.compile(r"[A-Za-zÀ-ÿ0-9]+")

def _tokenize(s: str) -> List[str]:
    return [w.lower() for w in WORD_RE.findall(s or "")]

def _must_include_ok(ingredients: str, must: List[str]) -> Tuple[bool, List[str]]:
    if not must:
        return True, []
    ing_tokens = set(_tokenize(ingredients))
    hits = [m for m in must if m.lower() in ing_tokens]
    return (len(hits) == len(must)), hits

def _build_reasons(matches: List[str], diet: str, popularity: int) -> List[str]:
    reasons = []
    if matches:
        reasons.append(f"matched tokens: {', '.join(sorted(set(matches)))}")
    if diet and diet != "none":
        reasons.append(f"diet filter: {diet}")
    reasons.append(f"popular: {popularity} views/likes")
    return reasons

def recommend_popularity(query: str, diet: str, must_include: List[str], k: int) -> List[Dict[str, Any]]:
    rows = list_recipes(diet=diet, limit=10000)
    out: List[Dict[str, Any]] = []
    for r in rows:
        ok, hits = _must_include_ok(r["ingredients"], must_include)
        if not ok:
            continue
        score = float(r.get("popularity") or 0)
        reasons = _build_reasons(hits, diet, r.get("popularity") or 0)
        out.append({
            "id": r["id"],
            "title": r["title"],
            "reasons": reasons,
            "score": score,
            "url": r.get("url"),
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:k]

def recommend_keyword(query: str, diet: str, must_include: List[str], k: int) -> List[Dict[str, Any]]:
    qtokens = _tokenize(query)
    qset = set(qtokens)
    rows = list_recipes(diet=diet, limit=10000)
    out: List[Dict[str, Any]] = []
    for r in rows:
        ok, must_hits = _must_include_ok(r["ingredients"], must_include)
        if not ok:
            continue
        title_tokens = set(_tokenize(r["title"]))
        ingr_tokens = set(_tokenize(r["ingredients"]))
        hits = sorted((qset & (title_tokens | ingr_tokens)))
        if not hits and qtokens:
            continue
        score = len(hits) + 0.0001 * float(r.get("popularity") or 0)
        reasons = _build_reasons(hits or must_hits, diet, r.get("popularity") or 0)
        out.append({
            "id": r["id"],
            "title": r["title"],
            "reasons": reasons,
            "score": score,
            "url": r.get("url"),
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:k]
