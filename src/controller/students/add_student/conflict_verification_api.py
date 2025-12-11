# src\controller\students\add_student\conflict_verification_api.py

from flask import session, request, jsonify, Blueprint
from sqlalchemy import or_

from src.model import ClassData, StudentsDB, StudentSessions

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required

from src.controller.students.utils.str_to_date import str_to_date
from src.controller.utils.get_gapped_rolls import get_gapped_rolls


conflict_verification_api_bp = Blueprint( 'conflict_verification_api_bp',   __name__)


@conflict_verification_api_bp.route('/api/conflict_verification', methods=["POST"])
@login_required
@permission_required('admission')
def verify_admission():

    data = request.get_json()

    school_id = session.get('school_id')
    current_session_id = session.get('session_id')

    # Initialize all fields to avoid UnboundLocalError
    pen = apaar = aadhaar = sr = admission_no = class_id = section = roll = admission_session = admission_year = None

    # Extract fields
    for item in data:
        field = item["field"]
        value = item["value"]

        if field == "PEN":
            pen = value

        elif field == "APAAR":
            apaar = value

        elif field == "AADHAAR":
            aadhaar = value

        elif field == "SR":
            sr = value

        elif field == "ADMISSION_NO":
            admission_no = value

        elif field == "CLASS":
            class_id = value

        elif field == "Section":
            section = value

        elif field == "ROLL":
            roll = int(value)  # ensure integer

        elif field == "admission_session_id":
            admission_session = str(value)

        elif field == "ADMISSION_DATE":
            admission_year = str(str_to_date(value)).split("-")[-1]

    # Validate admission year vs session
    if admission_year != admission_session:
        return jsonify({
            'message': (
                f"You gave Admission year '{admission_year}' and session '{admission_session}-{int(admission_session)+1}'. "
                f"Admission Date year must match admission session year."
            )
        }), 400

    # Validate Admission No Prefix consistency
    admission_no_prefix = str(admission_no)[:2]
    if admission_no_prefix != str(admission_session)[-2:]:
        return jsonify({
            'message': (
                f"Admission number '{admission_no}' does not match admission session '{admission_session}-{int(admission_session)+1}'. "
                f"Last two digits must match session year."
            )
        }), 400

    # Prepare conflict conditions
    global_conflict_conditions = []
    school_conflict_conditions = []

    if pen:
        global_conflict_conditions.append(StudentsDB.PEN == pen)
    if apaar:
        global_conflict_conditions.append(StudentsDB.APAAR == apaar)

    # SR is mandatory
    if sr:
        school_conflict_conditions.append(StudentsDB.SR == sr)
    else:
        return jsonify({'message': 'Please enter SR properly!'}), 400

    # Admission Number mandatory
    if admission_no:
        school_conflict_conditions.append(StudentsDB.ADMISSION_NO == admission_no)
    else:
        return jsonify({'message': 'Please enter Admission Number properly!'}), 400

    # Check Global Conflicts
    if global_conflict_conditions:
        global_conflict = (
            StudentsDB.query
            .join(StudentSessions, StudentsDB.id == StudentSessions.student_id)
            .filter(
                StudentsDB.school_id == school_id,
                StudentSessions.session_id == current_session_id,
                or_(*global_conflict_conditions)
            )
            .first()
        )

        if global_conflict:
            conflict_fields = []
            if pen and global_conflict.PEN == pen:
                conflict_fields.append("PEN")
            if apaar and global_conflict.APAAR == apaar:
                conflict_fields.append("APAAR")

            detailed_message = (
                f"Student '{global_conflict.STUDENTS_NAME}' (admission number: {global_conflict.ADMISSION_NO}, "
                f"SR: {global_conflict.SR}) already exists with the same {', '.join(conflict_fields)}."
            )

            return jsonify({
                'message': detailed_message,
                'conflicting_fields': conflict_fields,
                'conflicting_student': global_conflict.STUDENTS_NAME
            }), 400

    # Check School-Level Conflicts
    school_conflict = StudentsDB.query.filter(
        StudentsDB.school_id == school_id,
        or_(*school_conflict_conditions)
    ).first()

    if school_conflict:
        conflict_fields = []
        if sr and school_conflict.SR == sr:
            conflict_fields.append("SR")
        if admission_no and school_conflict.ADMISSION_NO == admission_no:
            conflict_fields.append("Admission number")

        return jsonify({
            'message': (
                f"The following field(s) already exist for student "
                f"'{school_conflict.STUDENTS_NAME}': {', '.join(conflict_fields)}."
            ),
            'conflicting_fields': conflict_fields,
            'conflicting_student': school_conflict.STUDENTS_NAME
        }), 400

    # Validate class + roll presence
    if not class_id or roll is None:
        return jsonify({'message': 'Missing Class, Section, or ROLL for session check.'}), 400

    # Retrieve available rolls
    available_rolls_dict = get_gapped_rolls(class_id, current_session_id)
    available_rolls = available_rolls_dict["gapped_rolls"] + [available_rolls_dict["next_roll"]]

    # Ensure rolls are integers
    available_rolls = [int(r) for r in available_rolls]

    if roll not in available_rolls:
        return jsonify({
            'message': (
                f"Roll number {roll} is not available in this class for the current session.\n"
                f"Available roll numbers: {sorted(available_rolls)}"
            )
        }), 400

    return jsonify({'message': 'Admission details are valid.'}), 200
