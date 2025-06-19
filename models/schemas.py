from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class TeamMember(BaseModel):
    name: str
    email: EmailStr
    role: str  # developer, analyst, qa_tester
    tasks: List[str]
    deadlines: List[datetime]
    progress: Optional[float] = 0.0  # Progress percentage

class Task(BaseModel):
    description: str
    deadline: datetime
    status: str  # not_started, in_progress, completed
    progress: float = 0.0

class ProgressReport(BaseModel):
    date: datetime
    team_members: List[TeamMember]
    overall_progress: float
    summary: str
    blockers: List[str]
    recommendations: List[str]

class EmailTemplate(BaseModel):
    subject: str
    body: str
    recipient: EmailStr
    cc: Optional[List[EmailStr]] = None

class SlackMessage(BaseModel):
    channel: str
    text: str
    blocks: Optional[List[dict]] = None 