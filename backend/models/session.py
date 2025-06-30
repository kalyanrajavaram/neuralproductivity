from app import db

class PomodoroSession(db.Model):
    __tablename__ = 'pomodoro_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    date = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    duration = db.Column(db.Integer, nullable=False)

    task = db.Column(db.String(100), nullable=False)
    task_category = db.Column(db.String(50), nullable=True)
    focus_score = db.Column(db.Float, nullable=True)
    user_rating = db.Column(db.Integer, nullable=True)
    achievements = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<PomodoroSession {self.date} - {self.task}>'

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date,
            "start_time": self.start_time,
            "duration": self.duration,
            "task": self.task,
            "task_category": self.task_category,
            "focus_score": self.focus_score,
            "user_rating": self.user_rating,
            "achievements": self.achievements
        }
