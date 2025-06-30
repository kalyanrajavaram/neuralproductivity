# routes/preferences.py
from flask import Blueprint, request, jsonify
from models.user import User
from app import db

preferences_bp = Blueprint('preferences', __name__)

@preferences_bp.route('/user/preferences', methods=['POST'])
def set_user_preferences():
    data = request.get_json()

    email = data.get('email')
    name = data.get('name')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    try:
        user = User.query.filter_by(email=email).first()
        if user:
            if name:
                user.name = name
        else:
            # Create a new user
            user = User(email=email, name=name)
            db.session.add(user)

        db.session.commit()
        return jsonify({
            "message": "User saved",
            "user": user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
