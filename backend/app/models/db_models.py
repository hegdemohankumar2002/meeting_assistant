from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime
import json
from app.database import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, index=True)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    transcript = Column(Text)
    summary = Column(Text)
    cleaning_used = Column(Integer, default=0)  # 0 = False, 1 = True (SQLite doesn't have boolean)
    
    # Storing structured data as JSON strings for simplicity in SQLite
    key_points = Column(Text)     # JSON list
    action_items = Column(Text)   # JSON list
    speakers = Column(Text)       # JSON list of dicts
    segments = Column(Text)       # JSON list of dicts
    insights = Column(Text, default="{}")  # JSON string: {decisions: [], agreements: [], conflicts: []}
    role_summaries = Column(Text, default="{}")  # JSON string: {executive: "", technical: ""}
    inferred_agenda = Column(Text) # Text of inferred agenda
    roadmap = Column(Text) # Markdown string of roadmap

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "upload_timestamp": self.upload_timestamp.isoformat() if self.upload_timestamp else None,
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
