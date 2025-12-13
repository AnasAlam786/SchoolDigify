from flask import Blueprint, request, jsonify, session

from src.model import StudentSessions
from src.model.StudentsDB import StudentsDB
from src import db

from .utils.watsapp_messages import fee_demand_message
from .utils.fetch_fee_data import fetch_fee_data

demand_fee_message_bp = Blueprint( 'demand_fee_message_bp',   __name__)


@demand_fee_message_bp.route('/api/get_demand_fee_message', methods=["GET"])
def get_demand_fee_message():
    try:
        phone = request.args.get("phone")
        student_session_id = request.args.get("student_session_id")

        if not student_session_id and not phone:
            return jsonify({"message": "student_session_id or phone is required"}), 400

        current_session_id = session["session_id"]
        school_id = session["school_id"]
        data = fetch_fee_data(session_id=current_session_id, school_id=school_id, student_session_ids=[student_session_id])

        if not data:
            return jsonify({"message": "No fee data found"}), 404
        
        phone = data[0]["phone"]

        # Generate WhatsApp demand message
        whatsapp_message = fee_demand_message(data)
        return jsonify({
            "phone_number": phone,
            "whatsapp_message": whatsapp_message,
            "status": "success"
        }), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Internal Server Error"}), 500
