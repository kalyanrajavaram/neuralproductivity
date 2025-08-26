from datetime import datetime
from extensions import db

class PomodoroSession(db.Model):
    __tablename__ = "pomodoro_sessions"
    __table_args__ = (
        db.Index("ix_sessions_user_id_started_at", "user_id", "started_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Prefer datetimes over strings
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)
    timezone = db.Column(db.String(64), nullable=True)   # e.g., 'America/Los_Angeles'
    total_duration_sec = db.Column(db.Integer, nullable=True)

    # UX metadata
    task = db.Column(db.String(100), nullable=False)
    task_category = db.Column(db.String(50), nullable=True)
    focus_score = db.Column(db.Float, nullable=True)   # optional roll-up across chunks
    user_rating = db.Column(db.Integer, nullable=True)
    achievements = db.Column(db.String(200), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="sessions")
    chunks = db.relationship(
        "VideoChunk",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def __repr__(self):
        return f"<PomodoroSession {self.id} user={self.user_id} task={self.task}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "timezone": self.timezone,
            "total_duration_sec": self.total_duration_sec,
            "task": self.task,
            "task_category": self.task_category,
            "focus_score": self.focus_score,
            "user_rating": self.user_rating,
            "achievements": self.achievements,
        }
