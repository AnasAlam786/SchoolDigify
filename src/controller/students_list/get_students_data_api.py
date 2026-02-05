# src/controller/students_list/get_students_data_api.py

from collections import Counter
from flask import jsonify, session, Blueprint
from sqlalchemy import String, case, cast, extract, func
from datetime import datetime

from src.model.RTEInfo import RTEInfo
from src.model.StudentsDB import StudentsDB
from src.model.StudentSessions import StudentSessions
from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess

from src import db
from src.controller.permissions.permission_required import permission_required
from src.controller.auth.login_required import login_required




get_students_data_api_bp = Blueprint('get_students_data_api_bp', __name__)


@get_students_data_api_bp.route('/api/get_students_data', methods=['GET'])
@login_required
@permission_required('student_list')
def get_students_data():
    school_id = session['school_id']
    selected_session = session['session_id']
    user_id = session["user_id"]

    # ---------------------------------------------------
    # 1. Determine classes the user has access to
    # ---------------------------------------------------
    classes_query = (
        db.session.query(ClassData)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .filter(ClassAccess.staff_id == user_id)
        .order_by(ClassData.id.asc())
    )

    classes = classes_query.all()
    class_ids = [cls.id for cls in classes]

    # ---------------------------------------------------
    # 2. Main student data query (single query)
    # ---------------------------------------------------
    data = db.session.query(
        StudentsDB.id,StudentsDB.STUDENTS_NAME,
        func.to_char(StudentsDB.DOB, 'Dy, DD Mon YYYY').label('DOB'),
        StudentsDB.AADHAAR, StudentsDB.FATHERS_NAME,
        StudentsDB.PEN, StudentsDB.GENDER,
        StudentsDB.IMAGE, StudentsDB.ADMISSION_NO,
        StudentsDB.admission_session_id,
        StudentsDB.PHONE, StudentsDB.Free_Scheme,
        StudentsDB.ADMISSION_SESSION, StudentsDB.ADMISSION_DATE,
        StudentSessions.ROLL,
        StudentSessions.id.label("student_session_id"),
        ClassData.CLASS, ClassData.Section, ClassData.display_order,
        RTEInfo.is_RTE,
        # NEW / OLD STATUS
        case(
            (StudentsDB.admission_session_id == selected_session, 'new'),
            else_='old'
        ).label('student_status')

    ).join(
        StudentSessions, StudentSessions.student_id == StudentsDB.id
    ).join(
        ClassData, StudentSessions.class_id == ClassData.id
    ).outerjoin(
        RTEInfo, RTEInfo.student_id == StudentsDB.id
    ).filter(
        StudentsDB.school_id == school_id,
        StudentSessions.session_id == selected_session,
        ClassData.id.in_(class_ids)
    ).order_by(
        ClassData.display_order.asc(),
        StudentSessions.ROLL.asc()
    ).all()

    # ---------------------------------------------------
    # 3. Compute statistics in Python
    # ---------------------------------------------------

    total_students = len(data)
    total_girls = sum(1 for s in data if s.GENDER.lower() == 'female')
    total_boys = total_students - total_girls  # faster than looping again

    # Assuming new students have ADMISSION_NO containing selected_session
    old_students = sum(1 for s in data if str(s.ADMISSION_NO)[:2] != str(selected_session)[-2:])
    new_students = total_students - old_students

    # ---------------------------------------------------
    # 4. Get previous year stats (one small query)
    # ---------------------------------------------------

    # get total students and old students from previous session from sql
    previous_year_students_total, old_students_prv = db.session.query(
        func.count(StudentsDB.id),  # total students
        func.sum(
            case(
                (func.substr(cast(StudentsDB.ADMISSION_NO, String), 1, 2) != str(selected_session-1)[-2:], 1),
                else_=0
            )
        )  # old students
    ).join(
        StudentSessions, StudentSessions.student_id == StudentsDB.id
    ).filter(
        StudentsDB.school_id == school_id,
        StudentSessions.session_id == selected_session - 1
    ).one()

    if previous_year_students_total is None:
        previous_year_students_total = 0
    if old_students_prv is None:
        old_students_prv = 0

    new_students_prev = previous_year_students_total - old_students_prv

    increased_students = total_students - previous_year_students_total
    total_growth_percentage = increased_students / previous_year_students_total * 100 if previous_year_students_total else 0
    new_students_growth_percentage = (new_students - new_students_prev) / new_students_prev * 100 if new_students_prev else 0
    

    # ---------------------------------------------------
    # 5. Final JSON response
    # ---------------------------------------------------
    # Convert SQLAlchemy Row objects to dictionaries
    students_list = [s._asdict() for s in data]


    return jsonify({
        'status': 'success',
        'students': students_list,
        'total_count': total_students,
        'stats': {
            'total_students': total_students,
            'total_girls': total_girls,
            'total_boys': total_boys,
            'new_students': new_students,
            'old_students': old_students,
            'increased_students': increased_students,
            'new_students_growth_percentage': new_students_growth_percentage,
            'previous_year_students_total': previous_year_students_total,
            'total_growth_percentage': total_growth_percentage,
            'new_students_prev': new_students_prev
        }
    })
