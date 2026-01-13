# src/controller/students/utils/student_service.py

from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from src import db
from src.model import StudentsDB, StudentSessions, ClassData, RTEInfo, Schools
from src.controller.students.utils.upload_image import upload_image, delete_image, move_image
from src.controller.utils.get_gapped_rolls import get_gapped_rolls
import time


class StudentService:
    @staticmethod
    def str_to_date(value) -> date | None:
        if isinstance(value, date):
            return value

        if not value:
            return None

        formats = ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y")
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def validate_admission_consistency(values: Dict[str, str]) -> Optional[str]:
        """Validate admission year, session, and number consistency."""

        admission_no = values.get("ADMISSION_NO", "")
        admission_session_raw = values.get("admission_session_id", "")
        admission_date_raw = values.get("ADMISSION_DATE", "")

        if admission_no is not None:
            admission_no = str(admission_no).strip()
        
        admission_date = StudentService.str_to_date(admission_date_raw)
        if not isinstance(admission_date, date):
            return "Invalid or missing Admission Date."

        # --- Parse session start year ---
        try:
            session_start_year = int(str(admission_session_raw).strip())
        except Exception:
            return "Invalid or missing Admission Session."
        
        # --- Define academic session range ---
        session_start_date = date(session_start_year, 4, 1)
        session_end_date = date(session_start_year + 1, 3, 31)

        # --- Validate admission date ---
        if not (session_start_date <= admission_date <= session_end_date):
            return (
                f"Admission Date ({admission_date}) must fall within "
                f"Academic Session {session_start_year}-{session_start_year + 1}."
            )

        # --- Validate admission number prefix ---
        if admission_no:
            prefix = admission_no[:2]
            expected_suffix = str(session_start_year)[-2:]

            if prefix != expected_suffix:
                return (
                    f"Admission Number prefix ({prefix}) must match "
                    f"session year suffix ({expected_suffix})."
                )

        return None

    @staticmethod
    def validate_class_order(adm_class_id: int, cur_class_id: int) -> Optional[str]:
        """Ensure admission class display_order < current class display_order."""
        orders = db.session.query(ClassData.id, ClassData.display_order).filter(
            ClassData.id.in_([adm_class_id, cur_class_id])
        ).all()
        order_map = {row.id: row.display_order or 0 for row in orders}
        if order_map.get(adm_class_id, 0) > order_map.get(cur_class_id, 0):
            return "Admission Class must be same or lower than Current Class."
        return None

    @staticmethod
    def check_unique_conflicts(values: Dict[str, str], school_id: int, school_fields: list, exclude_student_id: Optional[int] = None) -> Optional[str]:
        """Check for unique field conflicts."""

        school_filters = []        
        for field in school_fields:
            value = values.get(field, None)
            if value:
                school_filters.append(getattr(StudentsDB, field) == value)

        if school_filters:
            query = db.session.query(StudentsDB).filter(
                StudentsDB.school_id == school_id,
                or_(*school_filters)
            )
            if exclude_student_id:
                query = query.filter(StudentsDB.id != exclude_student_id)
            conflict = query.first()
            if conflict:
                conflicting = [f for f, v in zip(school_fields, [values.get(f, "") for f in school_fields]) if v and getattr(conflict, f) == v]
                return f"Student '{conflict.STUDENTS_NAME}' already has the same {', '.join(conflicting)}."

        return None

    @staticmethod
    def check_roll_availability(class_id: int, session_id: int, roll: int, exclude_student_id: Optional[int] = None) -> Optional[str]:
        """Check if roll is available in the class for the session."""
        available = get_gapped_rolls(class_id, session_id)
        gapped = available.get("gapped_rolls", [])
        next_r = available.get("next_roll")

        available_rolls = set(gapped)
        if next_r is not None:
            available_rolls.add(next_r)

        if exclude_student_id:
            # Allow keeping existing roll
            existing_roll = db.session.query(StudentSessions.ROLL).filter(
                StudentSessions.student_id == exclude_student_id,
                StudentSessions.session_id == session_id
            ).scalar()
            available_rolls.add(existing_roll)
            if existing_roll == roll:
                return None

        if roll not in available_rolls:
            return f"Roll {roll} is not available. Available: {sorted(available_rolls)}"

        return None

    @staticmethod
    def create_student(verified_data: List[Dict], image_b64: Optional[str], school_id: int, session_id: int) -> Tuple[Optional[int], Optional[str]]:
        """Create a new student with all related data."""
        data = {item["field"]: item["value"] for item in verified_data}

        # Prepare data
        studentsdb_data = {k: v for k, v in data.items() if k in StudentsDB.__table__.columns}
        sessions_data = {k: v for k, v in data.items() if k in StudentSessions.__table__.columns}
        rte_data = {k: v for k, v in data.items() if k in RTEInfo.__table__.columns}

        # Convert dates
        for field in ["DOB", "ADMISSION_DATE"]:
            if field in studentsdb_data and isinstance(studentsdb_data[field], str):
                try:
                    studentsdb_data[field] = datetime.strptime(studentsdb_data[field], "%d-%m-%Y").date()
                except ValueError:
                    return None, f"Invalid date format for {field}."

        studentsdb_data["school_id"] = school_id
        studentsdb_data["Admission_Class"] = data["CLASS"]

        sessions_data["class_id"] = data["CLASS"]
        sessions_data["session_id"] = session_id
        sessions_data["created_at"] = studentsdb_data["ADMISSION_DATE"]

        try:
            new_student = StudentsDB(**studentsdb_data)
            db.session.add(new_student)
            db.session.flush()

            session_row = StudentSessions(student_id=new_student.id, **sessions_data)
            rte_row = RTEInfo(student_id=new_student.id, **rte_data)
            db.session.add(session_row)
            db.session.add(rte_row)

            # Handle image
            if image_b64:
                school = Schools.query.filter_by(id=school_id).first()
                if school:
                    encoded = image_b64.split(",")[1]
                    image_id = upload_image(encoded, data.get("ADMISSION_NO"), school.students_image_folder_id)
                    new_student.IMAGE = image_id
            db.session.commit()

            return new_student.id, None
        except IntegrityError as e:
            db.session.rollback()
            return None, "Database integrity error. Possible duplicate data."
        except Exception as e:
            db.session.rollback()
            if 'image_id' in locals():
                delete_image(image_id)
            return None, f"Failed to create student: {str(e)}"

    @staticmethod
    def update_student(student_id: int, verified_data: List[Dict], image_b64: Optional[str], image_status: str, school_id: int, session_id: int) -> Optional[str]:
        """Update an existing student."""
        student = StudentsDB.query.filter_by(id=student_id).first()
        if not student:
            return "Student not found."

        data = {item["field"]: item["value"] for item in verified_data}

        studentsdb_updates = {k: v for k, v in data.items() if k in StudentsDB.__table__.columns}
        sessions_updates = {k: v for k, v in data.items() if k in StudentSessions.__table__.columns}
        rte_updates = {k: v for k, v in data.items() if k in RTEInfo.__table__.columns}

        # Convert dates
        for field in ["DOB", "ADMISSION_DATE"]:
            if field in studentsdb_updates and isinstance(studentsdb_updates[field], str):
                try:
                    studentsdb_updates[field] = datetime.strptime(studentsdb_updates[field], "%d-%m-%Y").date()
                except ValueError:
                    return f"Invalid date format for {field}."

        # Special mappings
        if "CLASS" in data:
            sessions_updates["class_id"] = data["CLASS"]
        if "Section" in data:
            sessions_updates["Section"] = data["Section"]
        if "ROLL" in data:
            sessions_updates["ROLL"] = data["ROLL"]

        try:
            # Update StudentsDB
            for k, v in studentsdb_updates.items():
                setattr(student, k, v)

            # Update or create session row
            session_row = StudentSessions.query.filter_by(student_id=student_id, session_id=session_id).first()
            if not session_row:
                session_row = StudentSessions(student_id=student_id, session_id=session_id)
                db.session.add(session_row)
            for k, v in sessions_updates.items():
                setattr(session_row, k, v)

            # Update or create RTE row
            rte_row = RTEInfo.query.filter_by(student_id=student_id).first()
            if not rte_row:
                rte_row = RTEInfo(student_id=student_id)
                db.session.add(rte_row)
            for k, v in rte_updates.items():
                setattr(rte_row, k, v)

            # Image handling
            deleted_folder = "1e8iHskcj2Vtv_Mg_Mtp4BzdHocuhLd_f"
            school = Schools.query.filter_by(id=school_id).first()
            if not school:
                return "School not found."

            if image_status == "updated" and image_b64:
                encoded = image_b64.split(",")[1]
                image_id = upload_image(encoded, student.ADMISSION_NO, school.students_image_folder_id)
                if student.IMAGE:
                    move_image(student.IMAGE, deleted_folder, rename=str(student_id))
                student.IMAGE = image_id
            elif image_status == "removed" and student.IMAGE:
                old_id = student.IMAGE
                student.IMAGE = None
                move_image(old_id, deleted_folder, rename=str(student_id))
            start = time.perf_counter()
            db.session.commit()
            end = time.perf_counter()
            print(f"Update student time: {end - start:.6f} seconds")
            return None
        except IntegrityError:
            db.session.rollback()
            return "Update failed due to data conflicts."
        except Exception as e:
            db.session.rollback()
            return f"Update failed: {str(e)}"