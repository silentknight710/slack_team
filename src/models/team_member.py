from pydantic import BaseModel
from typing import Optional

class TeamMember(BaseModel):
    email: str
    name: str
    role: str
    work_target: str
    deadline: str  # ISO format date string
    progress: Optional[str] = None