from datetime import datetime
import uuid
from extensions import db

def gen_uuid():
    return str(uuid.uuid4())

class VideoChunk(db.Model):
    """
    Each uploaded video file (≤30 min) belongs to a session and a user.
    Stores final .mp4 path and technical metadata for reproducibility.
    """
    __tablename__ = "video_chunks"
    __table_args__ = (
        db.Index("ix_chunks_session_id_index", "session_id", "index"),
        db.Index("ix_chunks_user_id_created_at", "user_id", "created_at"),
        db.Index("ix_chunks_sha256", "sha256", unique=True),
    )

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)  # uuid
    session_id = db.Column(db.Integer, db.ForeignKey("pomodoro_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    index = db.Column(db.Integer, default=0, nullable=False)  # 0,1,2…

    # Storage
    stored_path = db.Column(db.Text, nullable=False)   # absolute path to final .mp4
    size_bytes = db.Column(db.BigInteger, nullable=True)
    duration_sec = db.Column(db.Integer, nullable=True)
    sha256 = db.Column(db.String(64), nullable=True, unique=True)

    # Optional capture metadata
    resolution_w = db.Column(db.Integer, nullable=True)
    resolution_h = db.Column(db.Integer, nullable=True)
    fps = db.Column(db.Float, nullable=True)
    mime_type = db.Column(db.String(64), nullable=True)   # 'video/mp4'
    camera_label = db.Column(db.String(128), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = db.relationship("PomodoroSession", back_populates="chunks")
    user = db.relationship("User", back_populates="chunks")
    job = db.relationship("AnalysisJob", back_populates="chunk", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<VideoChunk {self.id} s={self.session_id} idx={self.index}>"
