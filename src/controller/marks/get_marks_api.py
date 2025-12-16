# src/controller/get_marks_api.py


from flask import session, request, jsonify, Blueprint, render_template
from sqlalchemy import exists 

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required
from src.model.ClassAccess import ClassAccess
from src import db

from src.controller.marks.utils.marks_processing import result_data
from src.controller.marks.utils.process_marks import process_marks

from bs4 import BeautifulSoup
# import time


get_marks_api_bp = Blueprint('get_marks_api_bp',   __name__)

@get_marks_api_bp.route('/get_marks_api', methods=["POST"])
@login_required
@permission_required('get_result')  # Assuming same permission as single download
def get_marks_api():
    school_id = session["school_id"]
    current_session_id = session["session_id"]
    user_id = session["user_id"]

    try:
        class_id = int(request.json.get("class_id"))
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid class selected."}), 400

    if not school_id or not current_session_id or not user_id:
        return jsonify({"message": "Unable to get session data, Please try to logout and login again!"}), 403


    has_access = db.session.query(
        exists().where(ClassAccess.staff_id == user_id)
    ).scalar()

    if not has_access:
        return jsonify({"message": "You are not authorized to access this class."}), 403
    
    extra_fields = {
        "StudentsDB": ["STUDENTS_NAME", "DOB", "FATHERS_NAME", "FATHERS_NAME"],
        "ClassData": ["CLASS"],
        "StudentSessions": ["ROLL", "class_id"]
    }

    student_marks_data = result_data(school_id, current_session_id, class_id, 
                                     extra_fields=extra_fields)
    
    # end_time = time.time()  # end timer
    # print(f"login_required decorator took {end_time - start_time:.6f} seconds to run")


    if not student_marks_data:
        return jsonify({"message": "No Data Found"}), 400
    
    student_marks = process_marks(student_marks_data, add_grades_flag=False, add_grand_total_flag=True)

    # # Print the structure of result student_marks_dict
    # import pprint
    # pprint.pprint(student_marks)
   

    html = render_template('show_marks.html', student_marks=student_marks)
    soup = BeautifulSoup(html,"lxml")
    content = soup.body.find('div',{'id':'results'}).decode_contents()

    return jsonify({"html":str(content)})
    