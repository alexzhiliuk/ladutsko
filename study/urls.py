from study import views
from django.urls import path


urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("teachers/", views.TeachersListView.as_view(), name="teachers"),
    path("teacher/<int:pk>/", views.TeacherEditView.as_view(), name="teacher"),
    path("teacher/delete/<int:pk>/", views.delete_teacher, name="teacher-delete"),
    path("teacher/add/", views.TeacherCreateView.as_view(), name="teacher-add"),

    path("students/", views.StudentsListView.as_view(), name="students"),
    path("student/<int:pk>/", views.StudentEditView.as_view(), name="student"),
    path("student/delete/<int:pk>/", views.delete_student, name="student-delete"),
    path("student/add/", views.StudentCreateView.as_view(), name="student-add"),

    path("applications/", views.ApplicationsListView.as_view(), name="applications"),
    path("application/<int:pk>/", views.ApplicationView.as_view(), name="application"),
    path("application/delete/<int:pk>/", views.delete_application, name="application-delete"),

    path("groups/", views.GroupsListView.as_view(), name="groups"),
    path("group/<int:pk>/", views.GroupEditView.as_view(), name="group"),
    path("group/<int:pk>/students/", views.GroupStudentsListView.as_view(), name="group-students"),
    path("group/delete/<int:pk>/", views.delete_group, name="group-delete"),
    path("group/add/", views.GroupCreateView.as_view(), name="group-add"),
    path("group/<int:pk>/add-subject", views.TeacherGroupSubjectCreateView.as_view(), name="group-add-subject"),
    path("group/<int:pk>/remove-subject", views.delete_teacher_group_subject, name="group-remove-subject"),
    path("group/exclude-student/<int:pk>/", views.exclude_student, name="group-exclude-student"),
    path("group/student-grade/<int:pk>/", views.StudentGradeView.as_view(), name="group-student-grade"),

    path("subjects/", views.SubjectsListView.as_view(), name="subjects"),
    path("subject/<int:pk>/", views.SubjectEditView.as_view(), name="subject"),
    path("subject/delete/<int:pk>/", views.delete_subject, name="subject-delete"),
    path("subject/add/", views.SubjectCreateView.as_view(), name="subject-add"),
    path("subjects/upload/", views.UploadSubjectsView.as_view(), name="subjects-upload"),

    path("lessons/", views.LessonsListView.as_view(), name="lessons"),
    path("lesson/<int:pk>/", views.LessonEditView.as_view(), name="lesson"),
    path("lesson/delete/<int:pk>/", views.delete_lesson, name="lesson-delete"),
    path("lesson/add/", views.LessonCreateView.as_view(), name="lesson-add"),
    path("lesson/upload/", views.UploadLessonsView.as_view(), name="lessons-upload"),
    path("lesson/remove-photo/<int:pk>/", views.delete_lesson_photo, name="lesson-remove-photo"),
    path("lesson/remove-video/<int:pk>/", views.delete_lesson_video, name="lesson-remove-video"),
    path("lesson/remove-file/<int:pk>/", views.delete_lesson_file, name="lesson-remove-file"),
    path("lesson/check-work/<int:pk>/", views.CheckStudentWork.as_view(), name="lesson-check-work"),

    path("tests/", views.TestsListView.as_view(), name="tests"),
    path("test/<int:pk>/", views.TestEditView.as_view(), name="test"),
    path("test/delete/<int:pk>/", views.delete_test, name="test-delete"),
    path("test/add/", views.TestCreateView.as_view(), name="test-add"),
    path("test/<int:pk>/question/add/", views.TestQuestionCreateView.as_view(), name="test-question-add"),
    path("test/<int:test_pk>/question/<int:question_pk>/", views.TestQuestionEditView.as_view(), name="test-question"),
    path("test/<int:test_pk>/question/<int:question_pk>/delete", views.delete_question, name="test-question-delete"),
    path("test/<int:test_id>/download-tries/", views.download_test_tries, name="test-download-tries"),

    path("test/try/<int:pk>/check/", views.CheckTestView.as_view(), name="test-try-check"),

    path("question/<int:pk>/add-answer-variant/", views.add_answer_variant, name="add-answer-variant"),
    path("question/<int:pk>/add-correct-text-answer/", views.add_correct_text_answer, name="add-correct-text-answer"),
    path("answer/delete/<int:pk>/", views.delete_answer, name="answer-delete"),

    path("teacher/my-group/", views.MyGroupListView.as_view(), name="my-group"),
    path("teacher/my-group/create/", views.MyGroupCreateView.as_view(), name="my-group-create"),
    path("teacher/my-subjects/", views.MySubjectsListView.as_view(), name="my-subjects"),
    path("teacher/my-subjects/create/", views.MySubjectCreateView.as_view(), name="my-subject-create"),
    path("teacher/my-subject/<int:pk>/", views.MySubjectEditView.as_view(), name="my-subject"),
    path("teacher/my-lessons/", views.MyLessonsListView.as_view(), name="my-lessons"),
    path("teacher/my-lessons/create/", views.MyLessonCreateView.as_view(), name="my-lesson-create"),
    path("teacher/my-lesson/<int:pk>/", views.MyLessonEditView.as_view(), name="my-lesson"),
    path("teacher/my-tests/", views.MyTestsListView.as_view(), name="my-tests"),
    path("teacher/my-subject/<int:pk>/add-to-group/", views.MySubjectAddToGroupView.as_view(), name="my-subject-add-to-group"),
    path("teacher/my-subject/<int:pk>/remove-from-group/", views.remove_my_subject_from_group, name="my-subject-remove-from-group"),


    path("subject/<int:subject_id>/remove-from-group/", views.remove_subject_from_group, name="remove-subject-from-group"),
    path("subject/<int:subject_id>/add-to-group/", views.add_subject_to_group, name="add-subject-to-group"),

    path("student/subject/<int:pk>/", views.StudentSubjectView.as_view(), name="student-subject"),
    path("student/lesson/<int:pk>/", views.StudentLessonView.as_view(), name="student-lesson"),
    path("student/lesson/<int:pk>/individual-work/", views.StudentIndividualWorkView.as_view(), name="student-individual-work"),
    path("student/test/<int:pk>/", views.StudentTestView.as_view(), name="student-test"),

    path("about/", views.about, name="about"),
]
