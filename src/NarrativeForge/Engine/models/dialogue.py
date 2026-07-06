from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class DialogueLine(BaseModel):
    character_id: UUID
    character_name: str
    text: str
    emotion: str = ""
    action: str = ""
    pause_after: float = 0.0


class DialogueExchange(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    lines: list[DialogueLine] = Field(default_factory=list)
    context: str = ""
    mood: str = ""


class DialogueResult(BaseModel):
    exchanges: list[DialogueExchange] = Field(default_factory=list)
    format: str = "text"
    formatted_text: str = ""
