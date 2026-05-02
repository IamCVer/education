from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import get_current_user
from app.models.user_model import User, UserRole
from teacher.backend.schemas import (
    ClarifyRequest,
    ClarifyResponse,
    GenerateRequest,
    GenerateResponse,
    PptStatusResponse,
    ReviseRequest,
    SessionCreateResponse,
    SessionStateResponse,
    UploadResponse,
)
from teacher.backend.services.intent_service import clarify_teacher_intent
from teacher.backend.services.interactive_service import (
    export_interactive_html,
    generate_interactive_content,
)
from teacher.backend.services.lesson_plan_service import (
    export_lesson_plan,
    generate_lesson_plan,
)
from teacher.backend.services.ppt_service import fetch_ppt_status, submit_ppt_task
from teacher.backend.services.rag_service import retrieve_knowledge, sanitize_retrievals
from teacher.backend.services.reference_service import save_reference_file
from teacher.backend.services.session_service import get_teacher_session_store


router = APIRouter()
TEACHER_ROOT = Path(__file__).resolve().parents[1]
GRAPH_RAG_FALLBACK_DIR = Path(__file__).resolve().parents[2] / "app" / "datasource"


def _ensure_teacher_access(current_user: User) -> None:
    if current_user.role not in {UserRole.TEACHER, UserRole.ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅教师或管理员可访问该模块")


def _load_owned_session(current_user: User, session_id: str) -> Dict[str, Any]:
    store = get_teacher_session_store()
    try:
        session = store.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="会话不存在") from exc
    if session["user_id"] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="无权访问该会话")
    return session


@router.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/session", response_model=SessionCreateResponse)
async def create_teacher_session(current_user: User = Depends(get_current_user)):
    _ensure_teacher_access(current_user)
    store = get_teacher_session_store()
    session = store.create_session(current_user.id)
    return session


@router.get("/session/{session_id}", response_model=SessionStateResponse)
async def get_teacher_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_access(current_user)
    session = _load_owned_session(current_user, session_id)
    session.setdefault("confirmation_card", {})
    session.setdefault("missing_fields", [])
    session.setdefault("last_revision_note", "")
    session.setdefault("summary_text", "")
    session.setdefault("assistant_suggestions", [])
    session["retrievals"] = sanitize_retrievals(session.get("retrievals", []))
    return session


@router.post("/clarify", response_model=ClarifyResponse)
async def clarify_teacher_request(
    request: ClarifyRequest,
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_access(current_user)
    store = get_teacher_session_store()
    _load_owned_session(current_user, request.session_id)

    store.append_message(request.session_id, "user", request.user_input)
    latest = store.get_session(request.session_id)
    result = await clarify_teacher_intent(
        request.user_input,
        latest.get("messages", []),
        latest.get("intent", {}),
    )
    store.append_message(request.session_id, "assistant", result["assistant_message"])
    store.update_session(
        request.session_id,
        {
            "intent": result["intent"],
            "confirmation_card": result["confirmation_card"],
            "missing_fields": result["missing_fields"],
            "summary_text": result["summary_text"],
            "assistant_suggestions": result["assistant_suggestions"],
        },
    )
    return result


@router.post("/upload", response_model=UploadResponse)
async def upload_teacher_reference(
    session_id: str = Form(...),
    purpose: str = Form(""),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_access(current_user)
    store = get_teacher_session_store()
    session = _load_owned_session(current_user, session_id)

    session_dir = Path(session["files_dir"])
    reference = await save_reference_file(file, session_dir, purpose)
    references = list(session.get("references", []))
    references.append(reference)
    store.update_session(session_id, {"references": references})
    return reference


async def _generate_all_assets(session: Dict[str, Any], request: GenerateRequest) -> Dict[str, Any]:
    intent = session.get("intent", {})
    references = session.get("references", [])
    query = " ".join(
        [
            intent.get("topic", ""),
            " ".join(intent.get("key_points", [])),
            request.revision_note,
        ]
    ).strip()
    retrievals = await retrieve_knowledge(query or intent.get("topic", ""), GRAPH_RAG_FALLBACK_DIR, limit=5)
    lesson_plan = {"html": "", "sections": {}}
    interactive = {"html": "", "questions": []}
    ppt_task = session.get("generation", {}).get("ppt_task", {})

    if request.regenerate_lesson_plan:
        lesson_plan = await generate_lesson_plan(intent, references, retrievals, request.revision_note)
    if request.regenerate_interactive:
        interactive = await generate_interactive_content(intent, request.revision_note)
    if request.regenerate_ppt:
        ppt_prompt = (
            f"教学主题：{intent.get('topic', '')}\n"
            f"适用对象：{intent.get('grade_level', '')}\n"
            f"教学目标：{'；'.join(intent.get('teaching_goals', []))}\n"
            f"知识重点：{'；'.join(intent.get('key_points', []))}\n"
            f"重点难点：{'；'.join(intent.get('difficult_points', []))}\n"
            f"讲授逻辑：{'；'.join(intent.get('teaching_flow', []))}\n"
            f"风格要求：{'；'.join(intent.get('style_requirements', []))}\n"
            f"互动设计：{'；'.join(intent.get('interaction_preferences', []))}\n"
            f"参考资料摘要：{'；'.join(item.get('summary', '') for item in references[:5])}\n"
            f"知识库补充：{'；'.join(item.get('text', '')[:120] for item in retrievals[:3])}\n"
            f"修改意见：{request.revision_note}"
        )
        try:
            ppt_task = await submit_ppt_task(ppt_prompt)
        except Exception as exc:
            ppt_task = {
                "sid": "",
                "status": "fail",
                "progress_text": "",
                "download_url": "",
                "error_message": str(exc),
            }

    exports_dir = Path(session["exports_dir"])
    lesson_plan_path = ""
    interactive_path = ""
    if lesson_plan.get("sections"):
        try:
            lesson_plan_path = str(export_lesson_plan(exports_dir, lesson_plan["sections"]))
        except Exception:
            lesson_plan_path = ""
    if interactive.get("html"):
        try:
            interactive_path = str(export_interactive_html(exports_dir, interactive["html"]))
        except Exception:
            interactive_path = ""

    return {
        "retrievals": retrievals,
        "references": references,
        "lesson_plan_preview": lesson_plan.get("html", ""),
        "interactive_html": interactive.get("html", ""),
        "ppt_task": ppt_task,
        "lesson_plan_path": lesson_plan_path,
        "interactive_path": interactive_path,
    }


@router.post("/generate", response_model=GenerateResponse)
async def generate_teacher_assets(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_access(current_user)
    store = get_teacher_session_store()
    session = _load_owned_session(current_user, request.session_id)

    result = await _generate_all_assets(session, request)
    store.update_session(
        request.session_id,
        {
            "retrievals": result["retrievals"],
            "generation": {
                "ppt_task": result["ppt_task"],
                "lesson_plan_preview": result["lesson_plan_preview"],
                "interactive_html": result["interactive_html"],
                "lesson_plan_path": result["lesson_plan_path"],
                "interactive_path": result["interactive_path"],
            },
            "last_revision_note": request.revision_note,
        },
    )
    return {
        "ppt_task": result["ppt_task"],
        "lesson_plan_preview": result["lesson_plan_preview"],
        "interactive_html": result["interactive_html"],
        "retrievals": result["retrievals"],
        "references": result["references"],
    }


@router.post("/revise", response_model=GenerateResponse)
async def revise_teacher_assets(
    request: ReviseRequest,
    current_user: User = Depends(get_current_user),
):
    return await generate_teacher_assets(
        GenerateRequest(
            session_id=request.session_id,
            regenerate_ppt=True,
            regenerate_lesson_plan=True,
            regenerate_interactive=True,
            revision_note=request.revision_note,
        ),
        current_user=current_user,
    )


@router.get("/ppt/{sid}", response_model=PptStatusResponse)
async def get_teacher_ppt_status(
    sid: str,
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_access(current_user)
    try:
        return await fetch_ppt_status(sid)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/download/lesson-plan/{session_id}")
async def download_teacher_lesson_plan(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_access(current_user)
    session = _load_owned_session(current_user, session_id)
    path = session.get("generation", {}).get("lesson_plan_path")
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="教案文件不存在")
    return FileResponse(path, filename="lesson-plan.docx")


@router.get("/download/interactive/{session_id}")
async def download_teacher_interactive(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_access(current_user)
    session = _load_owned_session(current_user, session_id)
    path = session.get("generation", {}).get("interactive_path")
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="互动内容文件不存在")
    return FileResponse(path, filename="interactive-content.html")
