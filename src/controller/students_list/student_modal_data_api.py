# src/controller/students/student_modal_data_api.py

from flask import render_template, session, request, Blueprint, jsonify

from sqlalchemy import func, case

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required
from src.model import StudentsDB
from src.model import ClassData
from src.model import StudentSessions

from src import db

student_modal_data_api_bp = Blueprint( 'student_modal_data_api_bp',   __name__)



@student_modal_data_api_bp.route('/student_modal_data_api', methods=["POST"])
@login_required
@permission_required('student_details')
def student_modal_data_api():
    data = request.json
    
    student_id = int(data.get('student_id'))
    phone = data.get('phone')  #replace by familyID


    student = db.session.query(
            StudentsDB.id, StudentsDB.STUDENTS_NAME, StudentsDB.AADHAAR,
            StudentsDB.FATHERS_NAME, StudentsDB.MOTHERS_NAME, StudentsDB.PHONE,
            StudentsDB.ADDRESS, StudentsDB.ADMISSION_DATE, StudentsDB.SR, StudentsDB.IMAGE,
            StudentsDB.GENDER, StudentsDB.PEN, StudentsDB.ADMISSION_NO, StudentsDB.EMAIL,
            StudentsDB.BLOOD_GROUP, StudentsDB.Caste, StudentsDB.Previous_School_Name,
            func.to_char(StudentsDB.ADMISSION_DATE, 'DD-MM-YYYY').label('ADMISSION_DATE'),
            func.to_char(StudentsDB.DOB, 'Dy, DD Month YYYY').label('DOB'),
            ClassData.CLASS,  # Get the class name from the ClassData table
            StudentSessions.ROLL
        ).join(
            StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
        ).join(
            ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
        ).filter(
            StudentsDB.PHONE == phone,
            StudentSessions.session_id == session["session_id"],
        ).order_by(
        case(
            (StudentsDB.id == student_id, 0),  # Place the matched student_id at the top
            else_=1
        )
    ).all()

    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404
    
    # Convert to dict for JSON response
    students_data = []
    for s in student:
        students_data.append({
            "id": s.id,
            "STUDENTS_NAME": s.STUDENTS_NAME,
            "AADHAAR": s.AADHAAR,
            "FATHERS_NAME": s.FATHERS_NAME,
            "MOTHERS_NAME": s.MOTHERS_NAME,
            "PHONE": s.PHONE,
            "ADDRESS": s.ADDRESS,
            "ADMISSION_DATE": s.ADMISSION_DATE,
            "SR": s.SR,
            "IMAGE": s.IMAGE,
            "GENDER": s.GENDER,
            "PEN": s.PEN,
            "ADMISSION_NO": s.ADMISSION_NO,
            "EMAIL": s.EMAIL,
            "BLOOD_GROUP": s.BLOOD_GROUP,
            "Caste": s.Caste,
            "Previous_School_Name": s.Previous_School_Name,
            "DOB": s.DOB,
            "CLASS": s.CLASS,
            "ROLL": s.ROLL
        })
    
    return jsonify({"success": True, "students": students_data})