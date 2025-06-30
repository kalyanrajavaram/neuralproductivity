from flask import Blueprint, request, jsonify
from models.session import PomodoroSession
from models.user import User
from app import db

pomodoro_bp = Blueprint('pomodoro', __name__)

@pomodoro_bp.route('/start-session', methods=['POST'])
def start_session():
    data = request.get_json()

    try:
        # Default or ML-recommended Pomodoro length
        recommended_duration = 25  # Could be updated by ML model later

      
        session = PomodoroSession(
            user_id=data['user_id'],
            date=data['date'],                # e.g., "2025-06-21"
            start_time=data['start_time'],    # e.g., "14:00"
            duration=recommended_duration,
            task=data['task'],
            task_category=data.get('task_category'),
            status="planned"                
        )

        db.session.add(session)
        db.session.commit()

        return jsonify({
            "message": "Pomodoro session started",
            "session_id": session.id,
            "recommended_duration": recommended_duration
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
        
@pomodoro_bp.route('/log-session', methods=['POST'])
def log_session():
    data = request.get_json()
    try:
        session = PomodoroSession(
            user_id=data['user_id'],
            date=data['date'],
            start_time=data['start_time'],
            duration=data['duration'],
            task=data['task'],
            task_category=data.get('task_category'),
            focus_score=data.get('focus_score'),
            user_rating=data.get('user_rating'),
            achievements=data.get('achievements')
        )
    
        db.session.add(session)
        db.session.commit()
        return jsonify({"message": "Session logged successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@pomodoro_bp.route('/get-sessions/<int:user_id>', methods=['GET'])
def get_sessions(user_id):
    try:
        sessions = PomodoroSession.query.filter_by(user_id=user_id).all()
        return jsonify([session.to_dict() for session in sessions]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
