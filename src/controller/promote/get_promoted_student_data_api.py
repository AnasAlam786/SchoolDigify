# src/controller/promoted_student_modal_api.py

from flask import request, jsonify, Blueprint, session

from sqlalchemy import func
from sqlalchemy.orm import aliased

from src import db
from src.model import StudentsDB
from src.model import StudentSessions
from src.model import ClassData

from src.controller.permissions.permission_required import permission_required
from src.controller.auth.login_required import login_required
from src.controller.utils.get_gapped_rolls import get_gapped_rolls


get_promoted_student_data_api_bp = Blueprint('get_promoted_student_data_api_bp', __name__)


@get_promoted_student_data_api_bp.route('/api/promote/promoted-student-data', methods=["POST"])
@login_required
@permission_required('promote_student')
def get_promoted_student_data():
    """
    Fetch a single already promoted student's data including promotion details based on
    the previous session data.
    
    Expected JSON payload:
    {
        "promoted_session_id": <id of record in StudentSessions table>
    }
    """

    data = request.get_json()

    # Validate input: ensure required keys exist
    if not data or "studentSessionID" not in data:
        return jsonify({"message": "Missing required parameters."}), 400
    
    try:
        promoted_session_id = int(data.get('studentSessionID'))
    except Exception as e:
        print("Invalid parameter format:", data)
        return jsonify({"message": "Invalid parameter format."}), 400
    
    try:
        school_id = session.get("school_id")
        if not school_id:
            return jsonify({"message": "School information not found."}), 400

        # Create aliases for self-join
        PromotedSession = aliased(StudentSessions)
        PreviousSession = aliased(StudentSessions)
        PreviousClass = aliased(ClassData)

        student_row = db.session.query(
            StudentsDB.id, StudentsDB.STUDENTS_NAME, StudentsDB.IMAGE, 
            StudentsDB.FATHERS_NAME, StudentsDB.PHONE,

            # Promoted (current) session
            ClassData.CLASS.label("promoted_class"),
            PromotedSession.ROLL.label("promoted_roll"),
            PromotedSession.id.label("promoted_session_id"),
            PromotedSession.class_id.label("promoted_class_id"),
            func.to_char(PromotedSession.created_at, 'YYYY-MM-DD').label("promoted_date"),

            # Previous session
            PreviousClass.CLASS.label("CLASS"),
            PreviousSession.ROLL.label("ROLL"),
            PreviousClass.grade_level.label("previous_grade_level"),

        ).join(
            PromotedSession, PromotedSession.student_id == StudentsDB.id
        ).join(
            ClassData, PromotedSession.class_id == ClassData.id
        ).join(
            PreviousSession, PreviousSession.student_id == StudentsDB.id
        ).join(
            PreviousClass, PreviousSession.class_id == PreviousClass.id
        ).filter(
            PromotedSession.id == promoted_session_id,
            PreviousSession.id != promoted_session_id  # exclude the current session
        ).limit(1).first()  # get the most recent previous session only
        
    except Exception as error:
        # Log error here if you have a logger configured
        print("Error fetching student data:", error)
        return jsonify({"message": "An error occurred while fetching student data."}), 500

    if student_row is None:
        return jsonify({"message": "Student not found"}), 404

    # Get available classes (previous class and above) for update
    previous_grade_level = student_row.previous_grade_level
    available_classes = (
        db.session.query(ClassData.id, ClassData.CLASS, ClassData.grade_level)
        .filter(
            ClassData.school_id == school_id,
            ClassData.grade_level >= previous_grade_level
        )
        .order_by(ClassData.grade_level.asc())
        .all()
    )
    
    result = student_row._asdict()
    result["available_classes"] = [
        {"id": c[0], "name": c[1], "grade_level": c[2]}
        for c in available_classes
    ]

    return jsonify(result), 200