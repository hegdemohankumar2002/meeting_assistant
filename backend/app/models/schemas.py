from pydantic import BaseModel

class TranscriptResponse(BaseModel):
    transcript: str
    summary: str
