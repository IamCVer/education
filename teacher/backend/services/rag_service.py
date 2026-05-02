from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


def tokenize(text: str) -> List[str]:
    return [token for token in re.split(r"[^\w\u4e00-\u9fff]+", text.lower()) if token]


def text_to_vector(text: str) -> Counter:
    return Counter(tokenize(text))


def cosine_similarity(left: Counter, right: Counter) -> float:
    if not left or not right:
        return 0.0
    shared = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    normalized = text.strip()
    if not normalized:
        return []
    chunks = []
    start = 0
    while start < len(normalized):
        end = start + chunk_size
        chunks.append(normalized[start:end])
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks


def sanitize_retrieval_text(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<think\b[^>]*>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def sanitize_retrieval_item(item: Dict[str, object]) -> Dict[str, object]:
    sanitized = dict(item)
    description = sanitize_retrieval_text(str(sanitized.get("description", "") or ""))
    text = sanitize_retrieval_text(str(sanitized.get("text", "") or ""))
    title = sanitize_retrieval_text(str(sanitized.get("title", "") or ""))
    sanitized["title"] = title
    sanitized["description"] = description
    sanitized["text"] = text or description or title
    return sanitized


def sanitize_retrievals(items: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    return [sanitize_retrieval_item(item) for item in items]


def rank_chunks(query: str, chunks: Iterable[str], limit: int = 5) -> List[Dict[str, object]]:
    query_vector = text_to_vector(query)
    ranked = []
    for text in chunks:
        score = cosine_similarity(query_vector, text_to_vector(text))
        keyword_bonus = sum(text.count(token) for token in tokenize(query))
        ranked.append({"text": text, "score": round(score + keyword_bonus, 4)})
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:limit]


def load_knowledge_chunks(base_dir: Path) -> List[Dict[str, str]]:
    chunks: List[Dict[str, str]] = []
    for path in sorted(base_dir.glob("**/*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".txt", ".md", ".csv"}:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for chunk in chunk_text(content):
            chunks.append({"source": path.name, "text": chunk})
    return chunks


async def _query_neo4j_entities(query: str, limit: int = 5) -> List[Dict[str, object]]:
    try:
        from app.data_access.graph_db import graph_db
    except Exception:
        return []

    terms = tokenize(query)
    if not terms:
        return []

    cypher = """
    MATCH (e:Entity)
    WHERE ANY(term IN $terms WHERE
        toLower(coalesce(e.title, e.name, '')) CONTAINS term OR
        toLower(coalesce(e.name, e.title, '')) CONTAINS term OR
        toLower(coalesce(e.description, '')) CONTAINS term
    )
    RETURN coalesce(e.title, e.name, '未命名节点') AS name,
           coalesce(e.description, '') AS description
    LIMIT $limit
    """
    records = await graph_db.execute_query(cypher, {"terms": terms, "limit": limit})
    results = []
    for record in records:
        name = record["name"]
        description = record["description"]
        if not name and not description:
            continue
        results.append(
            {
                "source": "Neo4j",
                "title": name or "未命名节点",
                "description": description or "",
                "text": description or name or "",
                "score": 1.0,
            }
        )
    return sanitize_retrievals(results)


async def retrieve_knowledge(query: str, base_dir: Path, limit: int = 5) -> List[Dict[str, object]]:
    neo4j_results = await _query_neo4j_entities(query, limit=limit)
    if neo4j_results:
        return sanitize_retrievals(neo4j_results)

    loaded = load_knowledge_chunks(base_dir)
    ranked = rank_chunks(query, [item["text"] for item in loaded], limit=limit)
    results = []
    for ranked_item in ranked:
        source = next(
            (item["source"] for item in loaded if item["text"] == ranked_item["text"]),
            "knowledge_base",
        )
        results.append(
            {
                "source": "Datasource",
                "title": source,
                "description": ranked_item["text"][:180],
                "text": ranked_item["text"],
                "score": ranked_item["score"],
            }
        )
    return sanitize_retrievals(results)
