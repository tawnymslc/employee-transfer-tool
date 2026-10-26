from pydantic import BaseModel
from typing import Optional


class MeetingAnalysisRequest(BaseModel):
    customer: str
    meeting_notes: str
    consultant_notes: Optional[str] = None

class ActionItem(BaseModel):
    task: str
    owner: Optional[str] = None
    due_date: Optional[str] = None

class ImplementationUpdate(BaseModel):
    customer: str
    summary: str

    decisions: list[str]
    technical_issues: list[str]

    client_action_items: list[ActionItem]
    internal_action_items: list[ActionItem]

    blockers: list[str]
    open_questions: list[str]
    next_steps: list[str]