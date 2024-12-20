# academic/models.py
from django.db import models


class User(models.Model):
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)

    class Meta:
        db_table = 'master'  # Ensure this matches your database table name
class ProgramMaster(models.Model):
    program_id = models.CharField(max_length=7, primary_key=True)
    program_code = models.CharField(max_length=4)
    program_name = models.CharField(max_length=150)
    program_type = models.CharField(max_length=1)
    program_mode = models.CharField(max_length=1)
    no_of_terms = models.IntegerField(null=True)
    total_credits = models.DecimalField(max_digits=7, decimal_places=3, null=True)
    max_number_of_fail_subjects = models.IntegerField(null=True)
    ug_pg = models.CharField(max_length=2)
    active = models.CharField(max_length=4)
    months_duration_in_english = models.CharField(max_length=100, null=True)
    months_duration_in_hindi = models.CharField(max_length=100, null=True)
    result_system = models.CharField(max_length=2)

    class Meta:
        db_table = 'program_master'
        managed = False

class CourseEvaluationComponent(models.Model):
    program_id = models.CharField(max_length=7)
    exam_date = models.CharField(max_length=5)
    evaluation_id = models.CharField(max_length=3)
    evaluation_id_name = models.CharField(max_length=10)
    group_id = models.CharField(max_length=3)
    course_code = models.CharField(max_length=8)
    maximum_marks = models.IntegerField()
    weightage = models.IntegerField()
    component_full_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'course_evaluation_component'
        managed = False
        unique_together = ('program_id', 'evaluation_id', 'group_id', 'course_code')

class StudentMarks(models.Model):
    university_code = models.CharField(max_length=4)
    entity_id = models.CharField(max_length=8)
    roll_number = models.CharField(max_length=10)
    program_course_key = models.CharField(max_length=14)
    evaluation_id = models.CharField(max_length=3)
    marks = models.IntegerField(null=True)
    grades = models.CharField(max_length=2, null=True)
    pass_fail = models.CharField(max_length=3, null=True)
    course_code = models.CharField(max_length=8)
    semester_start_date = models.DateField()
    semester_end_date = models.DateField()

    class Meta:
        db_table = 'student_marks'
        managed = False
        unique_together = ('roll_number', 'program_course_key', 'evaluation_id', 
                         'course_code', 'semester_start_date', 'semester_end_date')

class StudentMarksSummary(models.Model):
    university_code = models.CharField(max_length=4)
    entity_id = models.CharField(max_length=8)
    roll_number = models.CharField(max_length=10)
    program_course_key = models.CharField(max_length=14)
    semester_start_date = models.DateField()
    semester_end_date = models.DateField()
    total_internal = models.IntegerField(null=True)
    total_external = models.IntegerField(null=True)
    total_marks = models.IntegerField(null=True)
    course_code = models.CharField(max_length=8)
    internal_grade = models.CharField(max_length=3, null=True)
    external_grade = models.CharField(max_length=3, null=True)
    final_grade_point = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    earned_credits = models.DecimalField(max_digits=6, decimal_places=3, null=True)

    class Meta:
        db_table = 'student_marks_summary'
        managed = False
        unique_together = ('roll_number', 'program_course_key', 'course_code', 
                         'semester_start_date', 'semester_end_date')
        