# src/controller/students/utils/conflict_verification.py

from flask import session
from src.controller.students.utils.student_service import StudentService
from src.model import StudentsDB, StudentSessions


def verify_conflicts(verified_data, mode='add', student_id=None):
    """
    Unified conflict verification for student admission and update.

    Args:
        verified_data: List of dicts with 'field' and 'value'
        mode: 'add' or 'update'
        student_id: Required for update mode

    Returns:
        str: Error message if conflicts found, None otherwise
    """
    values = {item["field"]: item["value"] for item in verified_data}

    school_id = session.get("school_id")
    session_id = session.get("session_id")
    if not school_id or not session_id:
        return [{'message': "Session context missing."}]

    # Validate admission consistency
    error = StudentService.validate_admission_consistency(values)
    if error:
        return [{"message": error}]

    print(mode, values.get("student_status"))

    # Validate class order (only for old students in add mode, or always in update)
    if mode == 'add':
        student_status = values.get("student_status")
        if student_status == "old":
            try:
                adm_class = int(values.get("Admission_Class", ""))
                cur_class = int(values.get("CLASS", ""))
            except ValueError:
                return [{'message': "Invalid class selections of Admission class and Current class."}]
            error = StudentService.validate_class_order(adm_class, cur_class)
            if error:
                final_error = [{'field': 'Admission_Class', 'message': error},{'field': 'CLASS', 'message': error}]
                return final_error
        else:
            # For new fresh students, admission class should be same as current class
            try:
                adm_class = int(values.get("Admission_Class", ""))
                cur_class = int(values.get("CLASS", ""))
                if adm_class != cur_class:
                    final_error = [{'field': 'Admission_Class', 'message': "For new students, Admission Class must be same as Current Class."}]
                    return final_error
            except ValueError:
                return [{'message': "Invalid class selections."}]

    else:  # update mode
        # Check for past academic records - prevent changes to Admission Class and Session
        if not student_id:
            return [{'message': "Student ID required for update mode."}]
        
        student = StudentsDB.query.filter_by(id=student_id).first()
        if not student:
            return [{'message': "Student not found."}]
        
        # Check if student has past StudentSessions records (excluding current session)
        past_records = StudentSessions.query.filter(
            StudentSessions.student_id == student_id,
            StudentSessions.session_id != session_id
        ).first()
        
        if past_records:
            # Prevent changes to Admission_Class if past records exist
            original_admission_class = student.Admission_Class
            new_admission_class = values.get("Admission_Class")
            if new_admission_class is not None and str(original_admission_class) != str(new_admission_class):
                final_error = [{'field': 'Admission_Class', 'message': "Cannot modify Admission Class: Student has past academic records."}]
                return final_error

            # Prevent changes to admission_session_id if past records exist
            original_session_id = student.admission_session_id
            new_session_id = values.get("admission_session_id")
            if new_session_id is not None and str(original_session_id) != str(new_session_id):
                final_error = [{'field': 'admission_session_id', 'message': "Cannot modify Admission Session: Student has past academic records."}]
                return final_error

        try:
            adm_class = int(values.get("Admission_Class", ""))
            cur_class = int(values.get("CLASS", ""))
        except ValueError:
            return [{'message': "Invalid class selections."}]
        error = StudentService.validate_class_order(adm_class, cur_class)
        if error:
            final_error = [{'field': 'Admission_Class', 'message': error}, {'field': 'CLASS', 'message': error}]
            return final_error

    # Check unique conflicts
    exclude_id = student_id if mode == 'update' else None

    school_fields = ["SR", "ADMISSION_NO", "PEN", "AADHAAR", "APAAR"]

    error = StudentService.check_unique_conflicts(values, school_id, school_fields, exclude_student_id=exclude_id)
    if error:
        return [{'message': error}]

    # Check roll availability
    try:
        class_id = int(values.get("CLASS", ""))
        roll = int(values.get("ROLL", ""))
    except ValueError:
        return [{'message': "Invalid class or roll."}]
    error = StudentService.check_roll_availability(class_id, session_id, roll, exclude_student_id=exclude_id)
    if error:
        final_error = [{'field': 'ROLL', 'message': error}]
        return final_error

    return None