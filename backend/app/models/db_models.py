from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime
import json
from app.database import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String, default="Untitled Meeting")
    filename = Column(String, index=True)
    duration_seconds = Column(Integer, default=0)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    transcript = Column(Text)
    summary = Column(Text)
    cleaning_used = Column(Integer, default=0)  # 0 = False, 1 = True (SQLite compatible)
    
    # Storing structured data as JSON strings for SQLite compatibility
    key_points = Column(Text)     # JSON list
    action_items = Column(Text)   # JSON list
    speakers = Column(Text)       # JSON list of dicts
    segments = Column(Text)       # JSON list of dicts (with emotion=None now)
    insights = Column(Text, default="{}")   # JSON: {decisions: [], agreements: [], conflicts: []}
    role_summaries = Column(Text, default="{}")  # JSON: {executive: "", technical: ""}
    inferred_agenda = Column(Text)
    roadmap = Column(Text)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "filename": self.filename,
            "duration_seconds": self.duration_seconds,
            "upload_timestamp": self.upload_timestamp.isoformat() if self.upload_timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "transcript": self.transcript,
            "summary": self.summary,
            "key_points": json.loads(self.key_points) if self.key_points else [],
            "action_items": json.loads(self.action_items) if self.action_items else [],
            "speakers": json.loads(self.speakers) if self.speakers else [],
            "segments": json.loads(self.segments) if self.segments else [],
            "insights": json.loads(self.insights) if self.insights else {},
            "role_summaries": json.loads(self.role_summaries) if self.role_summaries else {},
            "inferred_agenda": self.inferred_agenda,
            "roadmap": self.roadmap,
        }
