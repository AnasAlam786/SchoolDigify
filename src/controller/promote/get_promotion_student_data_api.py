# src/controller/student_data_modal_api.py

from flask import session,  request, jsonify, Blueprint

from sqlalchemy import func, select, literal

from src import db
from src.model import StudentsDB
from src.model import StudentSessions
from src.model import ClassData

import datetime

from src.controller.permissions.permission_required import permission_required
from src.controller.auth.login_required import login_required
from src.controller.utils.get_gapped_rolls import get_gapped_rolls


get_student_promotion_data_api_bp = Blueprint('get_student_promotion_data_api_bp', __name__)


@get_student_promotion_data_api_bp.route('/api/promote/student-promotion-data', methods=["POST"])
@login_required
@permission_required('promote_student')
def get_student_promotion_data():
    """
    Fetch a single student's data along with promotion details
    based on the previous session.
    """

    # -------------------------
    # Validate request payload
    # -------------------------
    data = request.get_json()
    if not data or "student_id" not in data:
        return jsonify({"message": "Missing required parameters."}), 400

    try:
        student_id = int(data["student_id"])
    except:
        return jsonify({"message": "Invalid parameter format."}), 400

    # -------------------------
    # Validate session values
    # -------------------------
    try:
        school_id = session["school_id"]
        current_session_id = int(session["session_id"])
        previous_session_id = current_session_id - 1
    except (KeyError, ValueError):
        return jsonify({"message": "Session data is missing or corrupted. Please logout and login again!"}), 500


    # ----------------------------------------------------------------------
    # 1. Fetch student's current class info FROM PREVIOUS SESSION
    # ----------------------------------------------------------------------
    current_info = (
        db.session.query(StudentSessions.class_id,
                         ClassData.display_order,
                         ClassData.CLASS)
        .join(ClassData, ClassData.id == StudentSessions.class_id)
        .filter(StudentSessions.student_id == student_id,
                StudentSessions.session_id == previous_session_id)
        .first()
    )

    if not current_info:
        return jsonify({"message": "Student not found in previous session."}), 404

    current_class_id, current_display_order, current_class_name = current_info

    # ----------------------------------------------------------------------
    # 2. Fetch all possible classes (same or above)
    # ----------------------------------------------------------------------
    available_classes = (
        db.session.query(ClassData.id, ClassData.CLASS, ClassData.display_order)
        .filter(ClassData.school_id == school_id,
                ClassData.display_order >= current_display_order)
        .order_by(ClassData.display_order.asc())
        .all()
    )


    # ----------------------------------------------------------------------
    # 3. Determine next class (simple scan)
    # ----------------------------------------------------------------------
    next_class = None
    for c_id, c_name, d_order in available_classes:
        if d_order > current_display_order:
            next_class = (c_id, c_name)
            break

    if next_class:
        promoted_class_id, promoted_class_name = next_class
    else:
        # Student already in highest class
        promoted_class_id = current_class_id
        promoted_class_name = current_class_name


    # ----------------------------------------------------------------------
    # 4. Get available roll numbers for promoted class in CURRENT session
    # ----------------------------------------------------------------------
    available_rolls_data = get_gapped_rolls(promoted_class_id, current_session_id)
    gapped_rolls = available_rolls_data['gapped_rolls']
    next_roll = available_rolls_data['next_roll']

    # Default to next available roll
    promoted_roll = next_roll


    # ----------------------------------------------------------------------
    # 5. Fetch student base data (much simpler query)
    # ----------------------------------------------------------------------
    student_row = (
        db.session.query(
            StudentsDB.id,
            StudentsDB.STUDENTS_NAME,
            StudentsDB.IMAGE,
            StudentsDB.FATHERS_NAME,
            StudentsDB.PHONE,
            ClassData.CLASS,
            StudentSessions.ROLL,
            StudentSessions.id.label("student_session_id"),
            StudentSessions.class_id.label("current_class_id")
        )
        .join(StudentSessions, StudentSessions.student_id == StudentsDB.id)
        .join(ClassData, ClassData.id == StudentSessions.class_id)
        .filter(StudentsDB.id == student_id,
                StudentSessions.session_id == previous_session_id)
        .first()
    )

    if not student_row:
        return jsonify({"message": "Student not found"}), 404

    
    # Convert to dict
    result = student_row._asdict()

    
    # Inject promotion fields (same output as original)
    result["promoted_class"] = promoted_class_name
    result["promoted_class_id"] = promoted_class_id
    result["promoted_roll"] = promoted_roll
    result["promoted_date"] = datetime.date.today().strftime('%Y-%m-%d')

    
    # Add available classes and roll information
    result["available_classes"] = [
        {"id": c[0], "name": c[1], "display_order": c[2]}
        for c in available_classes
    ]

    # Add available roll numbers for the default promoted class
    result["available_rolls"] = {
        "gapped_rolls": gapped_rolls,
        "next_roll": next_roll
    }

    return jsonify(result), 200
