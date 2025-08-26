from datetime import datetime
from extensions import db

class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.Index("ix_users_email", "email", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    sessions = db.relationship(
        "PomodoroSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True,
    )
    chunks = db.relationship(
        "VideoChunk",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def __repr__(self):
        return f"<User {self.email}>"

    def to_dict(self):
        return {"id": self.id, "email": self.email, "name": self.name}
