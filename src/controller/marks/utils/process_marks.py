# src/controller/marks/utils/process_marks.py

from typing import OrderedDict
import pandas as pd
from .calc_grades import get_grade

def add_grand_total(group, exams):
    group["student_id"] = group.name

    df = group[group["exam_name"].isin(exams)]

    # --- Step 1: sum numeric marks per subject ---
    total_subject_marks = OrderedDict()
    for subj_dict in df["subject_marks_dict"]:
        for subj, mark in subj_dict.items():
            try:
                total_subject_marks[subj] = total_subject_marks.get(subj, 0) + int(mark)
            except:
                pass

    grand_total_row = df.iloc[0].copy()
    
    grand_total_row["exam_name"] = "G. Total"
    grand_total_row["exam_display_order"] = df["exam_display_order"].max() + 1
    grand_total_row["exam_total"] = sum(total_subject_marks.values())
    grand_total_row["weightage"] = df["weightage"].sum()
    grand_total_row["subject_marks_dict"] = total_subject_marks

    max_marks = int(grand_total_row["weightage"]) * len(grand_total_row["subject_marks_dict"])

    grand_total_row["percentage"] = int(
        (grand_total_row["exam_total"] / max_marks) * 100 if max_marks > 0 else 0
    )
    # grand_total_row["grade"], grand_total_row["remark"] = get_grade(grand_total_row["percentage"])
    # Concatenate both
    return pd.concat([group, pd.DataFrame([grand_total_row])], ignore_index=True)

def add_grades(group, exams):
    group["student_id"] = group.name

    # Only use rows whose exam_name is in the passed exams list
    df = group[group["exam_name"].isin(exams)]

    # Now df contains only the intended exams
    max_subject_marks = df["weightage"].sum()

    subject_grades = OrderedDict()
    subject_totals = OrderedDict()
    
    for subj_dict in df["subject_marks_dict"]:
        for subj, mark in subj_dict.items():
            try:
                subject_totals[subj] = subject_totals.get(subj, 0) + int(mark)
            except Exception as e:
                continue

            percentage = (subject_totals[subj] / max_subject_marks) * 100 if max_subject_marks > 0 else 0
            grade, _ = get_grade(percentage)
            subject_grades[subj] = grade

    grade_row = df.iloc[0].copy()
    max_total_marks = max_subject_marks * len(subject_grades)
    total_percentage = (sum(subject_totals.values()) / max_total_marks) * 100 if max_total_marks > 0 else 0
    grade, remark = get_grade(total_percentage)

    grade_row["exam_name"] = "Grades"
    grade_row["exam_display_order"] = df["exam_display_order"].max() + 2
    grade_row["exam_total"] = grade
    grade_row["weightage"] = "A,B,C,D,E"
    grade_row["percentage"] = None
    # grade_row["remark"] = remark
    grade_row["subject_marks_dict"] = subject_grades

    return pd.concat([group, pd.DataFrame([grade_row])], ignore_index=True)

def process_marks(student_marks_data, add_grades_flag=True, add_grand_total_flag=True):
    """
    Process raw marks data into final format.
    
    Args:
        student_marks_data: List of dicts from result_data
        add_grades_flag: Whether to add grades row
        add_grand_total_flag: Whether to add grand total row
    
    Returns:
        List of processed student marks dicts
    """
    if not student_marks_data:
        return []

    student_marks_df = pd.DataFrame(student_marks_data)

    # Extract Pure exam names and subjects
    exams = set(student_marks_df["exam_name"].unique())
    subjects = set()
    for exam in exams:
        exam_df = student_marks_df[student_marks_df["exam_name"] == exam]
        for subj_dict in exam_df["subject_marks_dict"]:
            subjects.update(subj_dict.keys())

    if add_grades_flag:
        student_marks_df = (
            student_marks_df
            .groupby("student_id", group_keys=False)
            .apply(lambda g: add_grades(g, exams), include_groups=False)
            .reset_index(drop=True)
        )

    if add_grand_total_flag:
        student_marks_df = (
            student_marks_df
            .groupby("student_id", group_keys=False)
            .apply(lambda g: add_grand_total(g, exams), include_groups=False)
            .reset_index(drop=True)
        )
    
    student_marks_df['percentage'] = student_marks_df['percentage'].fillna(0).round(1)
    student_marks_df['exam_total'] = pd.to_numeric(student_marks_df['exam_total'], errors='coerce').fillna(0).round(1)

    all_columns = student_marks_df.columns.tolist()
    non_common_colums = ['exam_name', 'subject_marks_dict', 'exam_total', 'percentage', 'exam_display_order', 'weightage', "exam_term"]
    common_columns = [col for col in all_columns if col not in non_common_colums]

    def exam_info_group(df):
        df_sorted = df.sort_values('exam_display_order', na_position='last')
        
        ordered_exams = OrderedDict()
        for _, row in df_sorted.iterrows():
            ordered_exams[row['exam_name']] = {
                'subject_marks_dict': row['subject_marks_dict'],
                'exam_total': row['exam_total'],
                'percentage': row['percentage'],
                'weightage': row['weightage'],
                'exam_term': row['exam_term'],
            }
        return ordered_exams

    student_marks_df[common_columns] = student_marks_df[common_columns].fillna("")
    student_marks_df = student_marks_df.groupby(common_columns).apply(exam_info_group, include_groups=False).reset_index(name="marks")

    student_marks_df = student_marks_df.sort_values(["CLASS", "ROLL"]).reset_index(drop=True)
    student_marks = student_marks_df.to_dict(orient='records')

    return student_marks