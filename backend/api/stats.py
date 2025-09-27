# routes_stats.py
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, Response
from sqlalchemy import func, cast, Date
from app import db
from models import PomodoroSession
import csv, io

stats_bp = Blueprint("stats", __name__)

@stats_bp.route("/api/stats/<int:user_id>")
def user_stats(user_id):
    # totals
    total_sessions = db.session.query(func.count(PomodoroSession.id)).filter_by(user_id=user_id).scalar()

    # total focus time (approx from segments)
    segs = db.session.query(PomodoroSession.segments_json).filter_by(user_id=user_id).all()
    total_focus_seconds = 0
    for (seg_json,) in segs:
        if not seg_json: continue
        for seg in seg_json:
            if seg.get("state") == "focused":
                total_focus_seconds += int(seg.get("duration_s", 0))

    # avg score
    avg_score = db.session.query(func.avg(PomodoroSession.focus_score)).filter_by(user_id=user_id).scalar() or 0

    # last 7 days trend (use created_at date)
    today = datetime.utcnow().date()
    seven = today - timedelta(days=6)
    trend_rows = (
        db.session.query(
            cast(PomodoroSession.created_at, Date).label("d"),
            func.avg(PomodoroSession.focus_score).label("avg_focus")
        )
        .filter(PomodoroSession.user_id == user_id, cast(PomodoroSession.created_at, Date) >= seven)
        .group_by("d").order_by("d")
        .all()
    )
    daily_focus_trend = [{"date": r.d.isoformat(), "avg_focus": float(r.avg_focus or 0)} for r in trend_rows]

    # recent sessions
    recent = (
        db.session.query(PomodoroSession)
        .filter_by(user_id=user_id)
        .order_by(PomodoroSession.created_at.desc())
        .limit(10).all()
    )
    recent_sessions = [{
        "id": s.id,
        "created_at": s.created_at.isoformat(),
        "task": s.task,
        "task_category": s.task_category,
        "focus_score": s.focus_score,
    } for s in recent]

    # category breakdown (time or count). Here: count per category
    cat_rows = (
        db.session.query(PomodoroSession.task_category, func.count(PomodoroSession.id))
        .filter(PomodoroSession.user_id == user_id)
        .group_by(PomodoroSession.task_category)
        .all()
    )
    category_breakdown = [{"category": c or "Uncategorized", "count": int(n)} for c, n in cat_rows]

    return jsonify({
        "totals": {
            "total_sessions": int(total_sessions),
            "total_focus_seconds": int(total_focus_seconds),
            "avg_focus_score": float(avg_score),
        },
        "daily_focus_trend": daily_focus_trend,
        "category_breakdown": category_breakdown,
        "recent_sessions": recent_sessions,
    })

@stats_bp.route("/api/stats/<int:user_id>/export.csv")
def export_csv(user_id):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id","created_at","task","task_category","focus_score"])
    for s in db.session.query(PomodoroSession).filter_by(user_id=user_id).order_by(PomodoroSession.created_at):
        writer.writerow([s.id, s.created_at.isoformat(), s.task or "", s.task_category or "", s.focus_score or ""])
    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv")
