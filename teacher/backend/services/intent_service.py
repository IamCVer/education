from __future__ import annotations

import json
import re
from typing import Any, Dict, List


REQUIRED_FIELDS = [
    "topic",
    "grade_level",
    "lesson_duration",
    "teaching_goals",
    "key_points",
]

FIELD_LABELS = {
    "topic": "教学主题",
    "grade_level": "适用年级",
    "subject": "学科",
    "lesson_duration": "课时/时长",
    "teaching_goals": "教学目标",
    "key_points": "重点知识点",
    "difficult_points": "难点",
    "teaching_flow": "讲授逻辑",
    "style_requirements": "风格要求",
    "interaction_preferences": "互动偏好",
}


def _normalize_list(value: Any) -> List[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = re.split(r"[，,；;、\n]+", value)
        return [item.strip() for item in parts if item.strip()]
    return [str(value).strip()]


def merge_intent_fields(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(old_data or {})
    for key, value in (new_data or {}).items():
        if isinstance(value, list):
            normalized = _normalize_list(value)
            if normalized:
                merged[key] = normalized
        elif value not in (None, "", {}, []):
            merged[key] = value
    return merged


def find_missing_fields(intent: Dict[str, Any]) -> List[str]:
    missing = []
    for field in REQUIRED_FIELDS:
        value = intent.get(field)
        if value in (None, "", []):
            missing.append(field)
    return missing


def build_clarify_question(missing_fields: List[str]) -> str:
    if not missing_fields:
        return "你的教学需求已经比较完整，我可以开始生成 PPT、教案和互动内容。"
    first = missing_fields[0]
    prompts = {
        "topic": "这次课的教学主题是什么？请尽量说得具体一些。",
        "grade_level": "请告诉我适用的年级或学生层次，例如大一、初二、考研冲刺。",
        "lesson_duration": "这节课准备上多长时间？是一课时还是多课时？",
        "teaching_goals": "你希望学生通过这节课达到哪些教学目标？",
        "key_points": "你最想突出哪些核心知识点？",
    }
    return prompts.get(first, f"请再补充一下“{FIELD_LABELS.get(first, first)}”这部分要求。")


def build_confirmation_card(intent: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": intent.get("topic") or "未命名课程",
        "summary": [
            {"label": FIELD_LABELS.get(key, key), "value": value}
            for key, value in intent.items()
            if value not in (None, "", [])
        ],
    }


def build_summary_text(intent: Dict[str, Any]) -> str:
    topic = intent.get("topic") or "当前课程"
    subject = intent.get("subject") or "未指定学科"
    grade_level = intent.get("grade_level") or "未指定对象"
    lesson_duration = intent.get("lesson_duration") or "时长待确认"
    goals = "、".join(intent.get("teaching_goals", [])[:2]) or "教学目标待补充"
    key_points = "、".join(intent.get("key_points", [])[:3]) or "核心知识点待补充"
    return (
        f"当前教学设计聚焦“{topic}”，学科为{subject}，面向{grade_level}，"
        f"预计{lesson_duration}。现阶段希望重点达成{goals}，并突出{key_points}。"
    )


def build_assistant_suggestions(intent: Dict[str, Any], missing_fields: List[str]) -> List[str]:
    suggestions: List[str] = []
    for field in missing_fields:
        if field == "grade_level":
            suggestions.append("请补充适用年级或学生层次，便于控制内容深浅。")
        elif field == "lesson_duration":
            suggestions.append("请补充课时或总时长，方便合理安排 PPT 页数和课堂活动。")
        elif field == "teaching_goals":
            suggestions.append("建议明确 2 到 3 个教学目标，例如知识理解、方法掌握或能力训练。")
        elif field == "key_points":
            suggestions.append("请补充本节课最想强调的 2 到 4 个核心知识点。")
        elif field == "topic":
            suggestions.append("请先明确本节课主题，最好细化到具体知识点。")

    if not intent.get("interaction_preferences"):
        suggestions.append("可以补充课堂互动形式，例如抢答、小测验、案例讨论或小游戏。")
    if not intent.get("style_requirements"):
        suggestions.append("可以补充呈现风格，例如图文并茂、案例驱动、偏简洁或偏学术。")
    if not intent.get("teaching_flow"):
        suggestions.append("如果你已有讲授顺序，可以告诉我导入、讲解、练习、总结的大致流程。")

    deduped: List[str] = []
    for item in suggestions:
        if item not in deduped:
            deduped.append(item)
    return deduped[:5]


def _simple_extract_from_text(text: str) -> Dict[str, Any]:
    lines = [line.strip() for line in re.split(r"[\n\r]+", text) if line.strip()]
    payload: Dict[str, Any] = {}

    def extract_value(patterns: List[str]) -> str:
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return ""

    topic_match = re.search(r"(主题|课程|内容)[:：]\s*(.+)", text)
    if topic_match:
        payload["topic"] = topic_match.group(2).strip()
    elif lines:
        payload["topic"] = lines[0][:80]

    subject_value = extract_value([r"(?:学科)[:：]\s*(.+)"])
    if subject_value:
        payload["subject"] = subject_value

    grade_value = extract_value([r"(?:年级|对象|适用学生|适用对象)[:：]\s*(.+)"])
    if grade_value:
        payload["grade_level"] = grade_value

    duration_value = extract_value([r"(?:时长|课时|时间)[:：]\s*(.+)"])
    if duration_value:
        payload["lesson_duration"] = duration_value

    goals_value = extract_value([r"(?:目标|教学目标)[:：]\s*(.+)"])
    if goals_value:
        payload["teaching_goals"] = _normalize_list(goals_value)

    key_points_value = extract_value([r"(?:知识点|核心知识点|重点知识点)[:：]\s*(.+)"])
    if key_points_value:
        payload["key_points"] = _normalize_list(key_points_value)

    difficult_points_value = extract_value([r"(?:重点难点|难点|重点)[:：]\s*(.+)"])
    if difficult_points_value:
        payload["difficult_points"] = _normalize_list(difficult_points_value)

    teaching_flow_value = extract_value([r"(?:讲授逻辑|教学过程|教学流程)[:：]\s*(.+)"])
    if teaching_flow_value:
        payload["teaching_flow"] = _normalize_list(teaching_flow_value)

    style_value = extract_value([r"(?:风格|呈现风格|风格要求)[:：]\s*(.+)"])
    if style_value:
        payload["style_requirements"] = _normalize_list(style_value)

    interaction_value = extract_value([r"(?:互动偏好|互动设计|课堂互动)[:：]\s*(.+)"])
    if interaction_value:
        payload["interaction_preferences"] = _normalize_list(interaction_value)

    payload.setdefault("key_points", _normalize_list(text[:120]))
    return payload


async def _llm_extract_intent(text: str, messages: List[Dict[str, str]], current_intent: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from app.providers.llm_provider import turbo_llm
    except Exception:
        return {}

    system_prompt = (
        "你是教学设计提炼助手。"
        "请根据教师输入、历史对话和已有结构化字段，提取并补全 JSON。"
        "只返回 JSON 对象，不要返回解释。"
        "字段包括: topic, grade_level, subject, lesson_duration, teaching_goals, "
        "key_points, difficult_points, teaching_flow, style_requirements, interaction_preferences。"
        "列表字段必须返回数组。"
    )
    user_prompt = json.dumps(
        {
            "current_input": text,
            "history": messages[-6:],
            "current_intent": current_intent,
        },
        ensure_ascii=False,
    )
    try:
        result = await turbo_llm.ainvoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        content = getattr(result, "content", "") or ""
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            return {}
        parsed = json.loads(match.group(0))
        normalized = {}
        for key, value in parsed.items():
            if key in {
                "teaching_goals",
                "key_points",
                "difficult_points",
                "teaching_flow",
                "style_requirements",
                "interaction_preferences",
            }:
                normalized[key] = _normalize_list(value)
            else:
                normalized[key] = str(value).strip() if value not in (None, "") else ""
        return normalized
    except Exception:
        return {}


async def clarify_teacher_intent(
    user_input: str,
    messages: List[Dict[str, str]],
    current_intent: Dict[str, Any],
) -> Dict[str, Any]:
    extracted = _simple_extract_from_text(user_input)
    llm_extracted = await _llm_extract_intent(user_input, messages, current_intent)
    merged = merge_intent_fields(current_intent, extracted)
    merged = merge_intent_fields(merged, llm_extracted)
    missing = find_missing_fields(merged)
    summary_text = build_summary_text(merged)
    assistant_suggestions = build_assistant_suggestions(merged, missing)
    assistant_message = (
        "我已经整理了你的教学需求。"
        if not missing
        else "我先帮你整理了现有需求，不过还有几点需要确认。"
    )
    assistant_message = f"{assistant_message}{build_clarify_question(missing)}"
    if assistant_suggestions:
        assistant_message = f"{assistant_message}\n建议：{assistant_suggestions[0]}"
    return {
        "assistant_message": assistant_message,
        "intent": merged,
        "missing_fields": missing,
        "ready_to_generate": not missing,
        "confirmation_card": build_confirmation_card(merged),
        "summary_text": summary_text,
        "assistant_suggestions": assistant_suggestions,
    }
