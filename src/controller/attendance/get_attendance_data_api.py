# src/controller/get_fee.py

from datetime import date, datetime
from sqlalchemy import and_, or_
from flask import session, request, jsonify, Blueprint

from src.controller.permissions.has_permission import has_permission
from src.model import StudentsDB, StudentSessions, ClassData
from src import db

from src.model.Attendance import Attendance
from src.model.AttendanceHolidays import AttendanceHolidays

from src.controller.permissions.permission_required import permission_required
from src.controller.auth.login_required import login_required

def parse_date(date_str):
    possible_formats = [
        "%Y-%m-%d",  # HTML input format
        "%d/%m/%Y",  # Indian format 1
        "%d-%m-%Y",  # Indian format 2
    ]

    for fmt in possible_formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except:
            continue

    return None

get_attendance_data_api_bp = Blueprint( 'get_attendance_data_api_bp',   __name__)

@get_attendance_data_api_bp.route('/api/get_attendance_data', methods=["GET"])
@login_required
@permission_required('attendance')
def get_attendance_data_api():

    class_id = request.args.get("classID")
    date_str = request.args.get("date")

    current_session = session["session_id"]
    school_id = session["school_id"]
    current_date = datetime.today().date()




    date = parse_date(date_str)
    if date is None:
        return jsonify({"message": "Invalid date format. Use DD/MM/YYYY or DD-MM-YYYY"}), 400
    
    if current_date != date:
        if not has_permission("mark_any_day_attendance"):
            return jsonify({"message": "Access denied. You are only authorized to record attendance for today only."}), 403


    holiday = AttendanceHolidays.query.filter(
        AttendanceHolidays.school_id == school_id,
        AttendanceHolidays.date == date,
        or_(
            AttendanceHolidays.class_id == class_id,
            AttendanceHolidays.class_id.is_(None)
        )
    ).first()


    if holiday:
        return jsonify({
            "message": "There is a Holiday on this date.",
            "holiday": True,
            "info": f"Attendance cannot be marked on {date.strftime('%A, %d %B %Y')} as classes are not held on the occasion of {holiday.name}. If you need to record attendance for a special session, please contact your administrator."

        }), 200

    # Don't allow marking attendance on Sundays (weekday(): Monday=0 ... Sunday=6)
    if date.weekday() == 6:
        return jsonify({
            "message": "Sunday — No Classes Scheduled",
            "holiday": True,
            "info": "Attendance cannot be marked on Sundays as classes are not held. If you need to record attendance for a special session, please contact your administrator."
        }), 200
        
    
    # Build query
    attendance_data = (
        db.session.query(
            StudentsDB.STUDENTS_NAME,
            StudentsDB.FATHERS_NAME,
            StudentsDB.IMAGE,
            StudentsDB.PHONE,
            ClassData.CLASS,
            StudentSessions.ROLL,
            StudentSessions.id.label("student_session_id"),
            Attendance.status.label("attendance_status"),
            Attendance.remark
        )
        .join(StudentSessions, StudentSessions.student_id == StudentsDB.id)
        .join(ClassData, ClassData.id == StudentSessions.class_id)
        .outerjoin(
            Attendance,
            and_(
                Attendance.student_session_id == StudentSessions.id,
                Attendance.date == date
            )
        )
        .filter(
            StudentSessions.class_id == class_id,
            StudentSessions.session_id == current_session
        )
        .order_by(StudentSessions.ROLL.asc())
    ).all()

    total_students = len(attendance_data)
    present = absent = half_day = not_marked = 0

    for attendance in attendance_data:
        if attendance.attendance_status == "PRESENT":
            present +=1 
        elif attendance.attendance_status == "ABSENT":
            absent +=1 
        elif attendance.attendance_status == "HALF_DAY":
            half_day +=1 
        else:
            not_marked += 1

    attendance_data = [dict(row._mapping) for row in attendance_data]

    # Pack everything neatly into one variable
    attendance_summary = {
        "date": date.strftime("%A, %d %B %Y"),
        "total": total_students,
        "present": present,
        "absent": absent,
        "half_day": half_day,
        "not_marked": not_marked
    }
    
    return jsonify({"attendance_data": attendance_data, "attendance_summary": attendance_summary}), 200


@get_attendance_data_api_bp.route('/api/get_absent_students', methods=["GET"])
@login_required
@permission_required('attendance')
def get_absent_students():
    class_id = request.args.get('classID')
    date = request.args.get('date')

    if not class_id or not date:
        return jsonify({"message": "Class ID and date are required"}), 400

    current_session = session["session_id"]
    school_id = session["school_id"]
    current_date = datetime.today().date()

    # Parse date
    date_obj = parse_date(date)
    if date_obj is None:
        return jsonify({"message": "Invalid date format. Use DD/MM/YYYY or DD-MM-YYYY"}), 400
    
    # Permission check for non-current dates
    if current_date != date_obj:
        if not has_permission("mark_any_day_attendance"):
            return jsonify({"message": "Access denied. You are only authorized to record attendance for today only."}), 403

    try:
        # Get class name
        class_record = ClassData.query.filter_by(
            id=class_id, 
            school_id=school_id
        ).first()
        
        if not class_record:
            return jsonify({"message": "Class not found"}), 404

        class_name = class_record.CLASS

        # Get absent students with attendance status ABSENT
        attendance_query = (
            db.session.query(
                StudentsDB.STUDENTS_NAME,
                # StudentsDB.FATHERS_NAME,
                StudentSessions.ROLL,
            )
            .join(StudentSessions, StudentSessions.student_id == StudentsDB.id)
            .join(Attendance, and_(
                Attendance.student_session_id == StudentSessions.id,
                Attendance.date == date_obj,
                Attendance.status == "ABSENT"
            ))
            .filter(
                StudentSessions.class_id == class_id,
                StudentSessions.session_id == current_session
            )
            .order_by(StudentSessions.ROLL.asc())
            .all()
        )

        absent_students = [dict(row._mapping) for row in attendance_query]

        # Format date for display
        formatted_date = date_obj.strftime('%A, %d %B %Y')

        return jsonify({
            'success': True,
            'class_name': class_name,
            'date': formatted_date,
            'absent_students': absent_students
        })

    except Exception as e:
        print(f"Error fetching absent students: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching absent students: {str(e)}'
        }), 500