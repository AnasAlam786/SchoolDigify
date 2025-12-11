import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from flask import session, request, jsonify, Blueprint
from sqlalchemy import or_

from src.controller.utils.get_gapped_rolls import get_gapped_rolls
from src.model import StudentsDB, StudentSessions
from src import db

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required
from src.model.ClassData import ClassData



def err(message: str, code: str = "validation_error", field: Optional[str] = None, http_status: int = 400):
    payload = {"status": "error", "error_code": code, "message": message}
    if field:
        payload["field"] = field
    return jsonify(payload), http_status


def parse_admission_year(admission_date_raw: Optional[str]) -> Optional[int]:
    """
    Try multiple common date formats and return the year (int).
    Return None if parsing fails.
    """
    if not admission_date_raw:
        return None

    admission_date_raw = str(admission_date_raw).strip()
    # If value already looks like a year (e.g. "2023"), accept it
    if re.fullmatch(r"\d{4}", admission_date_raw):
        return int(admission_date_raw)

    formats = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y", "%d %b %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(admission_date_raw, fmt).year
        except Exception:
            continue

    # fallback: split on - or / and take last token if 4 digits
    parts = re.split(r"[-/]", admission_date_raw)
    if parts:
        last = parts[-1]
        if re.fullmatch(r"\d{4}", last):
            return int(last)

    return None


update_conflict_verification_api_bp = Blueprint('update_conflict_verification_api_bp', __name__)


@update_conflict_verification_api_bp.route('/api/update_conflict_verification', methods=["POST"])
@login_required
@permission_required("update_student")
def verify_update_conflicts():
    """
    Validates the incoming 'verifiedData' for conflicts and consistency.

    Expects JSON:
      {
        "verifiedData": [{ "field": "...", "value": "..." }, ...],
        "student_id": <id>
      }

    Checks performed:
      - Admission year/session consistency
      - Admission number prefix consistency
      - Admission_Class <= CLASS (by display_order)
      - Global (within school) unique fields: AADHAAR, PEN, APAAR (excluding self)
      - School-unique fields: SR, ADMISSION_NO (excluding self)
      - Session-scoped roll availability (allow keeping existing roll)
    """
    body: Dict[str, Any] = request.get_json() or {}
    verified_items: List[Dict[str, Any]] = body.get("verifiedData", [])
    student_id = body.get("student_id")

    if not student_id:
        return err("Missing student id", code="missing_student_id", http_status=400)

    school_id = session.get("school_id")
    if not school_id:
        return err("Missing school context (school_id in session).", code="missing_school_context")

    current_session_id = session.get("session_id")
    if not current_session_id:
        return err("Missing session context (session_id in session).", code="missing_session_context")

    # Map values for quick lookup; preserve raw string form for comparisons
    values = {item["field"]: ("" if item.get("value") is None else str(item.get("value")).strip()) for item in verified_items}

    # ----------------------------
    # 0. Admission Year / Session consistency
    # ----------------------------
    admission_no = values.get("ADMISSION_NO", "")
    admission_session_raw = values.get("admission_session_id", "")
    admission_date_raw = values.get("ADMISSION_DATE", "")

    admission_year = parse_admission_year(admission_date_raw)
    try:
        admission_session_int = int(str(admission_session_raw).strip()) if admission_session_raw != "" else None
    except Exception:
        admission_session_int = None

    if admission_year is None or admission_session_int is None:
        return err("Invalid or missing ADMISSION_DATE or admission_session_id (expected a year).",
                   code="invalid_admission_date_or_session")

    # admission_session is typically year like 2023; comparing year parts
    if admission_year != admission_session_int:
        return err(
            f"You provided Admission date year '{admission_year}' but admission session '{admission_session_int}-{admission_session_int+1}'. Admission session and Admission Date must match!",
            code="admission_year_session_mismatch"
        )

    # Admission number prefix (last two digits must match session's last two digits)
    if admission_no:
        asmission_no_prefix = str(admission_no)[:2]  # original code took first two characters
        session_suffix = str(admission_session_int)[-2:]
        if asmission_no_prefix != session_suffix:
            return err(
                f"Admission number '{admission_no}' must start with session suffix '{session_suffix}' (for session {admission_session_int}-{admission_session_int+1}).",
                code="admission_no_prefix_mismatch",
                field="ADMISSION_NO"
            )

    # ----------------------------
    # 1. Admission_Class <= CLASS (by display_order)
    # ----------------------------
    adm_id_str = values.get("Admission_Class")
    cur_id_str = values.get("CLASS")
    if adm_id_str is None or cur_id_str is None or adm_id_str == "" or cur_id_str == "":
        return err("Admission Class and Current Class are required for existing students.", code="missing_class_fields")

    try:
        adm_id_int = int(adm_id_str)
        cur_id_int = int(cur_id_str)
    except (ValueError, TypeError):
        return err("Invalid class identifiers provided.", code="invalid_class_ids")

    # Fetch both ClassData.display_order in a single query
    class_rows = (
        db.session.query(ClassData.id, ClassData.display_order)
        .filter(ClassData.id.in_([adm_id_int, cur_id_int]))
        .all()
    )
    # create mapping
    order_map = {row.id: (row.display_order if row.display_order is not None else 0) for row in class_rows}
    adm_order = order_map.get(adm_id_int, 0)
    cur_order = order_map.get(cur_id_int, 0)

    if adm_order > cur_order:
        return err("For existing students, Admission class must be less than or equal to Current class (by display order).",
                   code="admission_class_gt_current")

    # ----------------------------
    # 2. Global-in-school Unique Check: AADHAAR, PEN, APAAR
    #    (unique across the same school, excluding the current student)
    # ----------------------------
    session_unique_fields = ["AADHAAR", "PEN", "APAAR"]
    session_filters = []
    for field in session_unique_fields:
        v = values.get(field)
        if v:
            session_filters.append(getattr(StudentsDB, field) == v)

    if session_filters:
        existing = (
            db.session.query(StudentsDB)
            .filter(
                StudentsDB.school_id == school_id,
                StudentsDB.id != student_id,
                or_(*session_filters)
            )
            .first()
        )
        if existing:
            conflicting_fields = [f for f in session_unique_fields if values.get(f) and getattr(existing, f) == values.get(f)]
            return err(
                f"Conflict for field(s) in school: {', '.join(conflicting_fields)} with student '{existing.STUDENTS_NAME}'.",
                code="conflict_global_fields"
            )

    # ----------------------------
    # 3. School-wide Unique Check: SR, ADMISSION_NO (required)
    # ----------------------------
    school_unique_fields = ["SR", "ADMISSION_NO"]
    school_filters = []
    for field in school_unique_fields:
        v = values.get(field)
        if not v or v == "":
            return err(f"'{field}' is required.", code="missing_field", field=field)
        school_filters.append(getattr(StudentsDB, field) == v)

    if school_filters:
        existing = (
            db.session.query(StudentsDB)
            .filter(
                StudentsDB.school_id == school_id,
                StudentsDB.id != student_id,
                or_(*school_filters)
            )
            .first()
        )
        if existing:
            conflicting_fields = [f for f in school_unique_fields if values.get(f) and getattr(existing, f) == values.get(f)]
            return err(
                f"Conflict in school for field(s): {', '.join(conflicting_fields)}. Student '{existing.STUDENTS_NAME}' already exists with same value(s).",
                code="conflict_school_fields"
            )

    # ----------------------------
    # INT-BASED Roll Check
    # ----------------------------
    class_id = values.get("CLASS")
    roll_raw = values.get("ROLL")

    if not all([class_id, roll_raw]):
        return err("CLASS and ROLL are required.", code="missing_roll_fields")

    try:
        requested_roll = int(roll_raw)
    except ValueError:
        return err("ROLL must be an integer.", code="invalid_roll_format", field="ROLL")

    old_roll = (
        db.session.query(StudentSessions.ROLL)
        .filter(
            StudentSessions.student_id == student_id,
            StudentSessions.session_id == current_session_id,
        )
        .scalar()
    )

    available = get_gapped_rolls(class_id, current_session_id)
    gapped = available.get("gapped_rolls") or []
    next_r = available.get("next_roll")

    available_rolls = set(gapped)
    if next_r is not None:
        available_rolls.add(next_r)

    if old_roll is not None and requested_roll == old_roll:
        pass
    elif requested_roll not in available_rolls:
        return err(
            f"Roll number {requested_roll} is not available.\n"
            f"Available roll(s): {sorted(available_rolls)}. Old roll: {old_roll}",
            code="roll_not_available"
        )

    # All checks passed
    return jsonify({"status": "ok", "message": "No conflicts found"}), 200