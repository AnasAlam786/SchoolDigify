from src.controller.marks.utils.process_marks import process_marks

# create sample data with interleaved display orders across terms
sample = [
    {"student_id":1, "CLASS":"A","ROLL":1, "exam_name":"Exam A", "exam_display_order":1, "exam_term":"Term 1", "weightage":100, "subject_marks_dict":{"Math":80}},
    {"student_id":1, "CLASS":"A","ROLL":1, "exam_name":"Exam B", "exam_display_order":4, "exam_term":"Term 1", "weightage":100, "subject_marks_dict":{"Math":90}},
    {"student_id":1, "CLASS":"A","ROLL":1, "exam_name":"Exam C", "exam_display_order":2, "exam_term":"Term 2", "weightage":100, "subject_marks_dict":{"Math":70}},
    {"student_id":1, "CLASS":"A","ROLL":1, "exam_name":"Exam D", "exam_display_order":3, "exam_term":"Term 2", "weightage":100, "subject_marks_dict":{"Math":60}},
]

print(process_marks(sample))
