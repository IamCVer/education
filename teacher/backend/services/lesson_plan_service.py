from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from teacher.backend.export.docx_exporter import export_lesson_plan_docx


REQUIRED_SECTIONS = [
    "教学主题",
    "教学目标",
    "重点难点",
    "教学过程",
    "教学方法",
    "课堂活动",
    "课后作业",
]


def normalize_lesson_plan_sections(payload: Dict[str, Any]) -> Dict[str, Any]:
    topic = payload.get("topic") or payload.get("教学主题") or "未命名课程"
    sections = {
        "教学主题": topic,
        "教学目标": payload.get("teaching_goals") or payload.get("教学目标") or ["理解核心概念", "能够完成课堂练习"],
        "重点难点": payload.get("重点难点") or payload.get("difficult_points") or ["需要重点讲解的概念与易错点"],
        "教学过程": payload.get("教学过程") or payload.get("teaching_flow") or ["课程导入", "核心讲授", "课堂互动", "总结提升"],
        "教学方法": payload.get("教学方法") or ["讲授法", "案例法", "互动问答"],
        "课堂活动": payload.get("课堂活动") or payload.get("interaction_preferences") or ["课堂问答", "随堂练习"],
        "课后作业": payload.get("课后作业") or ["完成课后练习并整理知识点笔记"],
    }
    for key in REQUIRED_SECTIONS:
        if sections[key] in (None, "", []):
            sections[key] = ["待教师补充"]
    return sections


async def _llm_generate_sections(prompt: str) -> Dict[str, Any]:
    try:
        from app.providers.llm_provider import max_llm
    except Exception:
        return {}

    system_prompt = (
        "你是教学教案生成助手。"
        "请严格返回 JSON，对应键为：教学主题、教学目标、重点难点、教学过程、教学方法、课堂活动、课后作业。"
        "除教学主题外，其他字段尽量返回数组。"
    )
    try:
        result = await max_llm.ainvoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        )
        content = getattr(result, "content", "") or ""
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            return {}
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def render_lesson_plan_html(sections: Dict[str, Any]) -> str:
    blocks = ['<div class="lesson-plan-preview">']
    for title, content in sections.items():
        blocks.append(f"<section><h3>{html.escape(title)}</h3>")
        if isinstance(content, list):
            blocks.append("<ul>")
            for item in content:
                blocks.append(f"<li>{html.escape(str(item))}</li>")
            blocks.append("</ul>")
        else:
            blocks.append(f"<p>{html.escape(str(content))}</p>")
        blocks.append("</section>")
    blocks.append("</div>")
    return "".join(blocks)


async def generate_lesson_plan(
    intent: Dict[str, Any],
    references: List[Dict[str, Any]],
    retrievals: List[Dict[str, Any]],
    revision_note: str = "",
) -> Dict[str, Any]:
    prompt_payload = {
        "intent": intent,
        "references": [{"summary": item.get("summary", ""), "purpose": item.get("purpose", "")} for item in references[:5]],
        "retrievals": retrievals[:5],
        "revision_note": revision_note,
    }
    llm_sections = await _llm_generate_sections(json.dumps(prompt_payload, ensure_ascii=False))
    sections = normalize_lesson_plan_sections({**intent, **llm_sections})
    return {
        "sections": sections,
        "html": render_lesson_plan_html(sections),
    }


def export_lesson_plan(session_exports_dir: Path, sections: Dict[str, Any]) -> Path:
    output_path = session_exports_dir / "lesson-plan.docx"
    return export_lesson_plan_docx(output_path, sections)
