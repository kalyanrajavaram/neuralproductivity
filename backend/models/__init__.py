# Import models so Flask-Migrate can discover them
from .user import User          # noqa: F401
from .pomodoro_session import PomodoroSession  # noqa: F401
from .video_chunk import VideoChunk            # noqa: F401
from .analysis_job import AnalysisJob          # noqa: F401
