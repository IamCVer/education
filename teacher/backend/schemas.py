from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TeacherMessage(BaseModel):
    role: str
    content: str


class TeacherIntent(BaseModel):
    topic: str = ""
    grade_level: str = ""
    subject: str = ""
    lesson_duration: str = ""
    teaching_goals: List[str] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)
    difficult_points: List[str] = Field(default_factory=list)
    teaching_flow: List[str] = Field(default_factory=list)
    style_requirements: List[str] = Field(default_factory=list)
    interaction_preferences: List[str] = Field(default_factory=list)


class SessionCreateResponse(BaseModel):
    session_id: str
    user_id: int
    intent: TeacherIntent
    messages: List[TeacherMessage] = Field(default_factory=list)
    references: List[Dict[str, Any]] = Field(default_factory=list)
    retrievals: List[Dict[str, Any]] = Field(default_factory=list)
    generation: Dict[str, Any] = Field(default_factory=dict)


class SessionStateResponse(SessionCreateResponse):
    confirmation_card: Dict[str, Any] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    last_revision_note: str = ""
    summary_text: str = ""
    assistant_suggestions: List[str] = Field(default_factory=list)


class ClarifyRequest(BaseModel):
    session_id: str
    user_input: str = Field(..., min_length=1, max_length=6000)


class ClarifyResponse(BaseModel):
    assistant_message: str
    intent: TeacherIntent
    missing_fields: List[str]
    ready_to_generate: bool
    confirmation_card: Dict[str, Any]
    summary_text: str = ""
    assistant_suggestions: List[str] = Field(default_factory=list)


class GenerateRequest(BaseModel):
    session_id: str
    regenerate_ppt: bool = True
    regenerate_lesson_plan: bool = True
    regenerate_interactive: bool = True
    revision_note: str = ""


class GenerateResponse(BaseModel):
    ppt_task: Dict[str, Any]
    lesson_plan_preview: str
    interactive_html: str
    retrievals: List[Dict[str, Any]]
    references: List[Dict[str, Any]]


class ReviseRequest(BaseModel):
    session_id: str
    revision_note: str = Field(..., min_length=1, max_length=3000)


class PptStatusResponse(BaseModel):
    sid: str
    status: str
    progress_text: str = ""
    download_url: str = ""
    error_message: str = ""
    total_pages: int = 0
    done_pages: int = 0


class UploadResponse(BaseModel):
    file_id: str
    file_name: str
    file_type: str
    purpose: str
    summary: str
    preview_text: str
    parse_status: str
