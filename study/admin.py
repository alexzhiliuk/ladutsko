from django.contrib import admin

from .models import (
    Group, Subject, TeacherGroupSubject, Lesson, LessonPhoto,
    LessonVideo, Test, Question, Answer, Try, StudentAnswer, StudentIndividualWork
)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["id", "number"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(TeacherGroupSubject)
class TeacherGroupSubjectAdmin(admin.ModelAdmin):
    list_display = ["teacher", "subject", "group"]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["name", "subject", "type"]


@admin.register(LessonPhoto)
class LessonPhotoAdmin(admin.ModelAdmin):
    list_display = ["lesson"]


@admin.register(LessonVideo)
class LessonVideoAdmin(admin.ModelAdmin):
    list_display = ["lesson"]


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["type", "text", "test"]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ["text", "correct", "question"]


@admin.register(Try)
class TryAdmin(admin.ModelAdmin):
    list_display = ["score", "user", "test"]


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ["user", "question", "answer", "student_try"]


@admin.register(StudentIndividualWork)
class StudentIndividualWorkAdmin(admin.ModelAdmin):
    list_display = ["user", "lesson", "score"]
