from datetime import datetime
from app import db


class Note(db.Model):
    """Note model for storing note data"""

    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(500), default="")
    color = db.Column(db.String(50), default="default")
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary for JSON API"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "tags": self.tags.split(",") if self.tags else [],
            "color": self.color,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_markdown(self):
        """Convert note to markdown format for export"""
        return f"# {self.title}\n\n{self.content}\n\n*Tags: {self.tags}*"
