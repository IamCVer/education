"""
互动内容生成接口

基于 llamacoder 思路，使用通义千问流式生成可运行的互动 HTML 内容
支持：知识测验、动画演示、互动游戏
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.api.deps import get_current_user
from app.models.user_model import User, UserRole
from app.providers.llm_provider import max_llm

logger = logging.getLogger(__name__)
router = APIRouter()


SYSTEM_PROMPT = """你是一个专业的教育互动内容生成专家。
根据教师提供的知识点，生成一个完整的、自包含的单文件 HTML 互动应用。

严格要求：
1. 只输出纯 HTML 代码，不要任何解释文字，不要 markdown 代码块标记
2. 代码必须完整可运行，所有 JS/CSS 内联在 HTML 中
3. 使用 vanilla JS，CSS 动画，不依赖外部库
4. 界面美观现代，配色和谐，适合学生使用
5. 必须有明确的互动操作和视觉反馈
6. 代码结构清晰，注释中文

不同内容类型的具体要求：

【知识测验 quiz】
- 生成5道选择题，每题4个选项
- 点击选项后立即显示对错反馈（颜色变化）
- 显示进度条和最终得分
- 答题完成后显示总结和知识要点回顾

【动画演示 animation】
- 用 CSS 动画 + JS 控制展示知识点的步骤/流程
- 提供「下一步」「上一步」「重播」按钮
- 每一步有文字说明
- 视觉化展示抽象概念

【互动游戏 game】
- 设计一个与知识点相关的小游戏（连连看/填空/拖拽/闯关）
- 有计时器和得分系统
- 3条命机制，游戏结束显示得分
- 简单易懂的游戏说明
"""


class GenerateRequest(BaseModel):
    knowledge_point: str = Field(..., min_length=2, max_length=500, description="知识点描述")
    content_type: str = Field(default="quiz", description="内容类型：quiz/animation/game")
    difficulty: Optional[str] = Field(default="medium", description="难度：easy/medium/hard")


@router.post("/interactive")
async def generate_interactive_content(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    流式生成互动教学内容（HTML代码）

    - 仅教师和管理员可调用
    - 使用 Server-Sent Events 流式返回生成的 HTML 代码
    - 前端用 iframe srcdoc 沙盒实时运行预览
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN, UserRole.STUDENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问内容生成功能"
        )

    content_type_map = {
        "quiz": "知识测验",
        "animation": "动画演示",
        "game": "互动游戏"
    }
    difficulty_map = {
        "easy": "简单（适合初学者）",
        "medium": "中等（适合有基础的学生）",
        "hard": "困难（适合进阶学生）"
    }

    content_type_cn = content_type_map.get(request.content_type, "知识测验")
    difficulty_cn = difficulty_map.get(request.difficulty, "中等")

    user_prompt = f"""知识点：{request.knowledge_point}
内容类型：{content_type_cn}
难度级别：{difficulty_cn}

请直接输出完整的 HTML 代码，不要任何其他内容。"""

    logger.info(f"Teacher {current_user.id} generating {request.content_type} for: {request.knowledge_point[:50]}")

    async def stream_html():
        try:
            async for chunk in max_llm.astream([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]):
                if chunk.content:
                    escaped = chunk.content.replace('\n', '\\n').replace('\r', '')
                    yield f"data: {escaped}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        stream_html(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*"
        }
    )

