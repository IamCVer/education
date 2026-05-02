from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List


def render_interactive_html(topic: str, questions: List[Dict[str, Any]]) -> str:
    cards = []
    for index, question in enumerate(questions, start=1):
        answer_value = html.escape(str(question.get("answer", "")), quote=True)
        options = "".join(
            f'<button class="option" data-answer="{answer_value}" onclick="checkAnswer(this)">{html.escape(str(option))}</button>'
            for option in question.get("options", [])
        )
        cards.append(
            f"""
            <div class="card">
              <div class="badge">题目 {index}</div>
              <h3>{html.escape(str(question.get("question", "")))}</h3>
              <div class="options">{options}</div>
            </div>
            """
        )
    return f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>{html.escape(topic)}互动练习</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; background:#f4f7fb; color:#1f2937; margin:0; padding:24px; }}
        .shell {{ max-width: 960px; margin: 0 auto; }}
        .hero {{ background: linear-gradient(135deg,#1d4ed8,#0f766e); color:white; padding:24px; border-radius:20px; }}
        .grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:16px; margin-top:20px; }}
        .card {{ background:white; border-radius:18px; padding:18px; box-shadow:0 14px 35px rgba(15,23,42,.08); }}
        .badge {{ display:inline-block; background:#dbeafe; color:#1d4ed8; border-radius:999px; padding:4px 10px; font-size:12px; margin-bottom:12px; }}
        .options {{ display:flex; flex-direction:column; gap:10px; }}
        .option {{ border:none; background:#eff6ff; color:#1e3a8a; border-radius:12px; padding:12px; cursor:pointer; text-align:left; }}
        .option.correct {{ background:#dcfce7; color:#166534; }}
        .option.wrong {{ background:#fee2e2; color:#991b1b; }}
      </style>
    </head>
    <body>
      <div class="shell">
        <div class="hero">
          <h1>{html.escape(topic)}互动练习</h1>
          <p>这是一个 demo 级互动内容页面，适合直接嵌入教学演示或下载后单独使用。</p>
        </div>
        <div class="grid">
          {''.join(cards)}
        </div>
      </div>
      <script>
        function checkAnswer(button) {{
          const value = button.textContent.trim();
          const answer = button.dataset.answer;
          if (value === answer) {{
            button.classList.add('correct');
          }} else {{
            button.classList.add('wrong');
          }}
        }}
      </script>
    </body>
    </html>
    """


async def _llm_generate_questions(prompt: str) -> List[Dict[str, Any]]:
    try:
        from app.providers.llm_provider import max_llm
    except Exception:
        return []
    system_prompt = (
        "你是课堂互动题目生成助手。"
        "请严格返回 JSON 数组，每项包含 question, options, answer。"
        "options 必须是 4 个选项。"
    )
    try:
        result = await max_llm.ainvoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        )
        content = getattr(result, "content", "") or ""
        match = re.search(r"\[.*\]", content, re.S)
        if not match:
            return []
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _fallback_questions(topic: str) -> List[Dict[str, Any]]:
    return [
        {
            "question": f"{topic}的课堂导入最适合先做什么？",
            "options": ["提出生活案例", "直接布置考试", "跳过主题", "只放结束页"],
            "answer": "提出生活案例",
        },
        {
            "question": f"讲解{topic}时，最需要教师强调哪类内容？",
            "options": ["核心概念与应用", "无关八卦", "随机闲聊", "只读标题"],
            "answer": "核心概念与应用",
        },
        {
            "question": "为了保证课堂互动，下面哪项更合适？",
            "options": ["设置随堂提问", "整节课静默", "取消练习", "只展示封面"],
            "answer": "设置随堂提问",
        },
    ]


async def generate_interactive_content(
    intent: Dict[str, Any],
    revision_note: str = "",
) -> Dict[str, Any]:
    topic = intent.get("topic") or "教学主题"
    prompt = json.dumps({"intent": intent, "revision_note": revision_note}, ensure_ascii=False)
    questions = await _llm_generate_questions(prompt)
    if not questions:
        questions = _fallback_questions(topic)
    html_content = render_interactive_html(topic, questions)
    return {"questions": questions, "html": html_content}


def export_interactive_html(session_exports_dir: Path, html_content: str) -> Path:
    output_path = session_exports_dir / "interactive-content.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    return output_path
