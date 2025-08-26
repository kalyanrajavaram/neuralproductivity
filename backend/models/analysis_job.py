from datetime import datetime
import uuid
from extensions import db

def gen_uuid():
    return str(uuid.uuid4())

class AnalysisJob(db.Model):
    """
    Tracks OpenFace + model pipeline per chunk.
    """
    __tablename__ = "analysis_jobs"
    __table_args__ = (
        db.Index("ix_jobs_status_updated", "status", "updated_at"),
    )

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)  # uuid
    chunk_id = db.Column(db.String(36), db.ForeignKey("video_chunks.id", ondelete="CASCADE"), unique=True, nullable=False)

    status = db.Column(db.String(16), default="queued", nullable=False)  # queued|running|done|failed
    au_csv_path = db.Column(db.Text, nullable=True)
    focus_score = db.Column(db.Float, nullable=True)
    error_msg = db.Column(db.Text, nullable=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    chunk = db.relationship("VideoChunk", back_populates="job")

    def __repr__(self):
        return f"<AnalysisJob {self.id} status={self.status}>"
