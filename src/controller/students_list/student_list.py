# src/controller/student_list.py

from flask import render_template, session, Blueprint
from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess

from src import db
from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required


student_list_bp = Blueprint('student_list_bp', __name__)


@student_list_bp.route('/student_list', methods=['GET'])
@login_required
@permission_required('student_list')
def student_list():

    school_id = session['school_id']
    user_id = session["user_id"]

    classes = (
        db.session.query(ClassData)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .filter(ClassAccess.staff_id == user_id)
        .order_by(ClassData.id.asc())
        .all()
    )
    return render_template(
        'student_list.html',
        data=[],
        classes=classes,
        total_students=0,
        total_girls=0,
        total_boys=0,
        new_students=0,
        old_students=0,
        class_counts={},
        total_growth_percentage=0,
        new_students_growth_percentage=0,
        increased_students=0,
        previous_year_students_total=0,
        new_students_prev=0
    )
