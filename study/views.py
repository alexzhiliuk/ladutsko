import pandas as pd
from datetime import datetime as dt
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.forms import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView

from accounts.forms import UserEditForm, UserCreateForm, ProfileEditForm
from accounts.models import Application
from .decorators.is_admin import admin_only
from .decorators.is_not_student import not_student
from .decorators.is_teacher import teacher_only
from .forms import (
    StudentForm, GroupForm, SubjectForm, LessonForm, QuestionForm, AnswerForm,
    ExcelForm, TeacherGroupSubjectForm,
    GroupForTeacherSubjectForm, TestForm, StudentWorkForm)
from .models import Group, TeacherGroupSubject, Subject, Lesson, LessonPhoto, Test, Question, Answer, Try, LessonVideo, \
    StudentAnswer, LessonFile, StudentIndividualWork


class IndexView(LoginRequiredMixin, View):
    menu = {
        "admin": {
            "Пользователи": {
                "Преподаватели": reverse_lazy("teachers"),
                "Студенты": reverse_lazy("students"),
            },
            "Заявки": reverse_lazy("applications"),
            "Группы": reverse_lazy("groups"),
            "Дисциплины": reverse_lazy("subjects"),
            "Занятия": reverse_lazy("lessons"),
            "Контроль знаний": reverse_lazy("tests"),
        },
        "teacher": {
            "Группы": reverse_lazy("my-group"),
            "Дисциплины": reverse_lazy("my-subjects"),
            "Занятия": reverse_lazy("my-lessons"),
            "Контроль знаний": reverse_lazy("tests"),
        }
    }

    def get(self, request, *args, **kwargs):

        user = request.user
        if user.profile.type == 1:
            return render(request, "study/index.html", {"menu": self.menu["admin"]})
        if user.profile.type == 2:
            return render(request, "study/index.html", {"menu": self.menu["teacher"]})
        if user.profile.type == 3:
            return render(
                request,
                "study/index.html",
                {
                    "menu": {subject.name_for_student: reverse_lazy("student-subject", kwargs={"pk": subject.pk}) for subject in user.group_set.first().subjects.all()}
                }
            )


@method_decorator(admin_only, name="dispatch")
class TeachersListView(LoginRequiredMixin, ListView):
    model = User
    context_object_name = "objects"
    template_name = "study/teachers.html"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(profile__type=2)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


@method_decorator(admin_only, name="dispatch")
class TeacherEditView(LoginRequiredMixin, View):

    def post(self, request, pk, *args, **kwargs):
        teacher = get_object_or_404(User, pk=pk)
        user_form = UserEditForm(instance=teacher, data=request.POST)
        profile_form = ProfileEditForm(instance=teacher.profile, data=request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.username = user.email
            user.save()

            profile_form.save()

            messages.success(request, "Преподаватель успешно изменен!")

        return redirect(reverse("teacher", kwargs={"pk": pk}))

    def get(self, request, pk, *args, **kwargs):
        teacher = get_object_or_404(User, pk=pk)
        user_form = UserEditForm(instance=teacher)
        profile_form = ProfileEditForm(instance=teacher.profile)

        return render(request, "study/teacher-edit.html", {
            "user_form": user_form,
            "profile_form": profile_form,
            "teacher": teacher,
        })


@method_decorator(admin_only, name="dispatch")
class TeacherCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user_form = UserCreateForm(request.POST)
        profile_form = ProfileEditForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():

            new_user = user_form.save(commit=False)
            new_user_password = user_form.cleaned_data.get("password")
            new_user.set_password(new_user_password)
            new_user.username = new_user.email
            new_user.save()

            profile = new_user.profile
            profile.middle_name = profile_form.cleaned_data.get("middle_name")
            profile.type = 2
            profile.save()

            try:
                send_mail(
                    "Данные для входа",
                    f"Логин - ваша почта: {new_user.email}\nПароль: {new_user_password}",
                    settings.EMAIL_HOST_USER,
                    [new_user.email])
            except Exception as err:
                print(err)
                messages.error(request, "Не получилось отправить письмо на почту")

            messages.success(request, "Преподаватель успешно создан!")
            return redirect(reverse("teachers"))

        return redirect(reverse("teacher-add"))

    def get(self, request, *args, **kwargs):
        user_form = UserCreateForm()
        profile_form = ProfileEditForm()
        return render(request, "study/teacher-add.html", {
            "user_form": user_form,
            "profile_form": profile_form,
        })


@admin_only
def delete_teacher(request, pk):

    teacher = get_object_or_404(User, pk=pk)
    username = teacher.username
    teacher.delete()
    messages.success(request, f"Преподаватель {username} удален!")

    return redirect(reverse("teachers"))


@method_decorator(admin_only, name="dispatch")
class StudentsListView(LoginRequiredMixin, ListView):
    model = User
    context_object_name = "objects"
    template_name = "study/students.html"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(profile__type=3)


@method_decorator(admin_only, name="dispatch")
class StudentEditView(LoginRequiredMixin, View):

    def post(self, request, pk, *args, **kwargs):
        student = get_object_or_404(User, pk=pk)
        user_form = UserEditForm(instance=student, data=request.POST)
        profile_form = StudentForm(instance=student.profile, data=request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.username = user.email
            user.save()

            group = profile_form.cleaned_data.get("group")
            user_group = user.group_set.first()
            profile_form.save()

            if group:
                if not(user in group.students.all()):
                    if user_group:
                        user_group.students.remove(user)
                    group.students.add(user)
            else:
                if user_group:
                    user_group.students.remove(user)

            messages.success(request, "Пользователь успешно изменен!")

        return redirect(reverse("student", kwargs={"pk": pk}))

    def get(self, request, pk, *args, **kwargs):
        student = get_object_or_404(User, pk=pk)
        user_form = UserEditForm(instance=student)
        profile_form = StudentForm(instance=student.profile)

        student_group = student.group_set.first()
        groups = Group.objects.all()

        return render(request, "study/student-edit.html", {
            "user_form": user_form,
            "profile_form": profile_form,
            "student_group": student_group,
            "groups": groups,
            "student": student,
        })


@method_decorator(admin_only, name="dispatch")
class StudentCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user_form = UserCreateForm(request.POST)
        profile_form = StudentForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():

            new_user = user_form.save(commit=False)
            new_user_password = user_form.cleaned_data.get("password")
            new_user.set_password(new_user_password)
            new_user.username = new_user.email
            new_user.save()

            profile = new_user.profile
            profile.middle_name = profile_form.cleaned_data.get("middle_name")
            profile.type = 3
            profile.save()

            group = profile_form.cleaned_data.get("group")
            if group:
                group.students.add(new_user)

            try:
                send_mail(
                    "Данные для входа",
                    f"Логин - ваша почта: {new_user.email}\nПароль: {new_user_password}",
                    settings.EMAIL_HOST_USER,
                    [new_user.email])
            except Exception as err:
                print(err)
                messages.error(request, "Не получилось отправить письмо на почту")

            messages.success(request, "Студент успешно создан!")
            return redirect(reverse("students"))

        return redirect(reverse("student-add"))

    def get(self, request, *args, **kwargs):
        user_form = UserCreateForm()
        profile_form = StudentForm()
        groups = Group.objects.all()
        return render(request, "study/student-add.html", {
            "user_form": user_form,
            "profile_form": profile_form,
            "groups": groups,
        })


@admin_only
def delete_student(request, pk):

    student = get_object_or_404(User, pk=pk)
    username = student.username
    student.delete()
    messages.success(request, f"Студент {username} удален!")

    return redirect(reverse("students"))


@method_decorator(admin_only, name="dispatch")
class ApplicationsListView(LoginRequiredMixin, ListView):
    model = Application
    context_object_name = "objects"
    template_name = "study/applications.html"


@method_decorator(admin_only, name="dispatch")
class ApplicationView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        application = get_object_or_404(Application, pk=pk)
        user_form = UserCreateForm(initial={
            "first_name": application.first_name,
            "last_name": application.last_name,
            "email": application.email
        })
        profile_form = StudentForm(initial={
            "middle_name": application.middle_name,
            "group": application.group_number
        })
        groups = Group.objects.all()

        if not(Group.objects.filter(number=application.group_number).first()):
            messages.error(request, "Пользователь указал несуществующую группу!")

        return render(request, "study/application.html", {
            "user_form": user_form,
            "profile_form": profile_form,
            "groups": groups,
            "application": application
        })


@admin_only
def delete_application(request, pk):

    application = get_object_or_404(Application, pk=pk)
    email = application.email
    application.delete()
    messages.success(request, f"Заявка от {email} удалена!")

    return redirect(reverse("applications"))


@method_decorator(admin_only, name="dispatch")
class TeacherGroupSubjectCreateView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        group = get_object_or_404(Group, pk=pk)
        form = TeacherGroupSubjectForm(request.POST)
        if form.is_valid():
            new_subject = form.save(commit=False)
            new_subject.group = group
            new_subject.save()
            messages.success(request, "У группы появилась новая дисциплина!")

        return redirect(reverse("group", kwargs={"pk": pk}))


@admin_only
def delete_teacher_group_subject(request, pk):

    subject = get_object_or_404(TeacherGroupSubject, pk=pk)
    group_pk = subject.group.pk
    subject.delete()
    messages.success(request, f"У группы удалена одна из дисциплин!")

    return redirect(reverse("group", kwargs={"pk": group_pk}))


@method_decorator(admin_only, name="dispatch")
class GroupStudentsListView(LoginRequiredMixin, ListView):
    model = User
    context_object_name = "students"
    template_name = "study/group/students-list.html"

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(Group, pk=kwargs.get("pk"))
        return super(GroupStudentsListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.group.students.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = self.group
        return context


@method_decorator(admin_only, name="dispatch")
class GroupsListView(LoginRequiredMixin, ListView):
    model = Group
    context_object_name = "objects"
    template_name = "study/group/list.html"


@method_decorator(admin_only, name="dispatch")
class GroupEditView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        group = get_object_or_404(Group, pk=pk)
        form = GroupForm(instance=group, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Группа успешно изменена!")
        return redirect(reverse("group", kwargs={"pk": pk}))

    def get(self, request, pk, *args, **kwargs):
        group = get_object_or_404(Group, pk=pk)

        form = GroupForm(instance=group)
        subjects_form = TeacherGroupSubjectForm()

        teachers = User.objects.filter(profile__type=2)
        subjects = Subject.objects.all()

        return render(
            request,
            "study/group/edit.html",
            {
                "form": form,
                "subjects_form": subjects_form,
                "group": group,
                "teachers": teachers,
                "subjects": subjects,
            }
        )


@method_decorator(admin_only, name="dispatch")
class GroupCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = GroupForm(request.POST)
        if form.is_valid():

            form.save()
            messages.success(request, "Группа успешно создана!")

        return redirect(reverse("groups"))

    def get(self, request, *args, **kwargs):
        form = GroupForm()
        teachers = User.objects.filter(profile__type=2)
        return render(request, "study/group/add.html", {"form": form, "teachers": teachers})


@admin_only
def delete_group(request, pk):

    group = get_object_or_404(Group, pk=pk)
    number = group.number
    group.delete()
    messages.success(request, f"Группа {number} удалена!")

    return redirect(reverse("groups"))


@method_decorator(admin_only, name="dispatch")
class SubjectsListView(LoginRequiredMixin, ListView):
    model = Subject
    context_object_name = "objects"
    template_name = "study/subjects/list.html"


@method_decorator(admin_only, name="dispatch")
class SubjectEditView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        subject = get_object_or_404(Subject, pk=pk)
        form = SubjectForm(instance=subject, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Дисциплина успешно изменена")

        return redirect(reverse("subject", kwargs={"pk": pk}))

    def get(self, request, pk, *args, **kwargs):
        subject = get_object_or_404(Subject, pk=pk)
        form = SubjectForm(instance=subject)
        teachers = User.objects.filter(profile__type=2)
        groups = Group.objects.all()
        return render(
            request, "study/subjects/edit.html",
            {
                "form": form,
                "subject": subject,
                "teachers": teachers,
                "groups": groups
            }
        )


@method_decorator(admin_only, name="dispatch")
class SubjectCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = SubjectForm(data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Дисциплина успешно создана")

        return redirect(reverse("subjects"))

    def get(self, request, *args, **kwargs):
        form = SubjectForm()
        teachers = User.objects.filter(profile__type=2)
        groups = Group.objects.all()
        return render(
            request,
            "study/subjects/add.html",
            {
                "form": form,
                "teachers": teachers,
                "groups": groups
            }
        )


@not_student
def delete_subject(request, pk):

    subject = get_object_or_404(Subject, pk=pk)
    name = subject.name
    subject.delete()
    messages.success(request, f"Дисциплина {name} удалена!")

    return redirect(reverse("subjects"))


@method_decorator(admin_only, name="dispatch")
class LessonsListView(LoginRequiredMixin, ListView):
    model = Lesson
    context_object_name = "objects"
    template_name = "study/lesson/list.html"

    def get_queryset(self):
        qs = super().get_queryset()
        subject_pk = self.request.GET.get("subject_pk")
        if subject_pk:
            subject = get_object_or_404(TeacherGroupSubject, pk=subject_pk)
            qs = qs.filter(subject=subject)
        return qs

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', '')
        # validate ordering here
        return ordering


@method_decorator(admin_only, name="dispatch")
class LessonEditView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        lesson = get_object_or_404(Lesson, pk=pk)
        form = LessonForm(instance=lesson, data=request.POST, files=request.FILES)
        if form.is_valid():
            edited_lesson = form.save(commit=False)
            if edited_lesson.type == "CW" and not edited_lesson.test:
                messages.error(request, "У контрольной работы должен быть тест")
                return redirect(reverse("lesson", kwargs={"pk": pk}))
            if edited_lesson.type == "CW" and not edited_lesson.test.can_be_control:
                messages.error(request, "У контрольной работы тест должен состоять только из текстовых вопросов")
                return redirect(reverse("lesson", kwargs={"pk": pk}))
            edited_lesson.save()

            photos_field = request.FILES.getlist("photos")
            videos_field = request.FILES.getlist("videos")
            files_field = request.FILES.getlist("files")

            if photos_field:
                for photo in photos_field:
                    LessonPhoto.objects.create(photo=photo, lesson=lesson)
            if videos_field:
                for video in videos_field:
                    LessonVideo.objects.create(video=video, lesson=lesson)
            if files_field:
                for file in files_field:
                    LessonFile.objects.create(file=file, lesson=lesson)

            messages.success(request, "Занятие изменено!")
        return redirect(reverse("lesson", kwargs={"pk": pk}))

    def get(self, request, pk, *args, **kwargs):
        lesson = get_object_or_404(Lesson, pk=pk)
        form = LessonForm(instance=lesson)
        subjects = TeacherGroupSubject.objects.all()
        tests = Test.objects.filter(lesson__isnull=True)
        types = Lesson.type.field.choices
        photos = lesson.photos.all()
        videos = lesson.videos.all()
        files = lesson.files.all()

        return render(request, "study/lesson/edit.html", {
            "form": form,
            "lesson": lesson,
            "subjects": subjects,
            "tests": tests,
            "types": types,
            "photos": photos,
            "videos": videos,
            "files": files,
        })


@method_decorator(admin_only, name="dispatch")
class LessonCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = LessonForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_lesson = form.save(commit=False)

            if new_lesson.type == "CW" and not new_lesson.test:
                messages.error(request, "У контрольной работы должен быть тест")
                return redirect(reverse("lesson-add"))
            if new_lesson.type == "CW" and not new_lesson.test.can_be_control:
                messages.error(request, "У контрольной работы тест должен состоять только из текстовых вопросов")
                return redirect(reverse("lesson-add"))

            new_lesson.save()

            photos_field = request.FILES.getlist("photos")
            videos_field = request.FILES.getlist("videos")
            files_field = request.FILES.getlist("files")

            if photos_field:
                for photo in photos_field:
                    LessonPhoto.objects.create(photo=photo, lesson=new_lesson)
            if videos_field:
                for video in videos_field:
                    LessonVideo.objects.create(video=video, lesson=new_lesson)
            if files_field:
                for file in files_field:
                    LessonFile.objects.create(file=file, lesson=new_lesson)

            messages.success(request, "Занятие создано!")

        return redirect(reverse("lessons"))

    def get(self, request, *args, **kwargs):

        form = LessonForm()
        subjects = TeacherGroupSubject.objects.all()
        tests = Test.objects.filter(lesson__isnull=True)
        types = Lesson.type.field.choices

        return render(request, "study/lesson/add.html", {
            "form": form,
            "subjects": subjects,
            "tests": tests,
            "types": types
        })


@admin_only
def delete_lesson_photo(request, pk):

    photo = get_object_or_404(LessonPhoto, pk=pk)
    lesson_pk = photo.lesson.pk
    photo.delete()
    messages.success(request, "Фотография удалена!")

    return redirect(reverse("lesson", kwargs={"pk": lesson_pk}))


@admin_only
def delete_lesson_video(request, pk):

    video = get_object_or_404(LessonVideo, pk=pk)
    lesson_pk = video.lesson.pk
    video.delete()
    messages.success(request, "Видеоролик удален!")

    return redirect(reverse("lesson", kwargs={"pk": lesson_pk}))


@admin_only
def delete_lesson_file(request, pk):
    file = get_object_or_404(LessonFile, pk=pk)
    lesson_pk = file.lesson.pk
    file.delete()
    messages.success(request, "Файл удален!")

    return redirect(reverse("lesson", kwargs={"pk": lesson_pk}))


@not_student
def delete_lesson(request, pk):

    lesson = get_object_or_404(Lesson, pk=pk)
    name = lesson.name
    lesson.delete()
    messages.success(request, f"Занятие {name} удалено!")

    return redirect(reverse("lessons"))


@method_decorator(not_student, name="dispatch")
class CheckStudentWork(LoginRequiredMixin, View):

    def post(self, request, pk, *args, **kwargs):
        work = get_object_or_404(StudentIndividualWork, pk=pk)

        score = request.POST.get("work-score")
        work.score = score
        work.save()

        messages.success(request, f"Работа студента {work.user} проверена")

        if request.user.profile.type == 1:
            return redirect(reverse("lesson", kwargs={"pk": work.lesson.pk}))
        return redirect(reverse("my-lesson", kwargs={"pk": work.lesson.pk}))

    def get(self, request, pk, *args, **kwargs):
        work = get_object_or_404(StudentIndividualWork, pk=pk)

        return render(request, "study/lesson/check-work.html", {
            "work": work,
        })


@method_decorator(not_student, name="dispatch")
class TestsListView(LoginRequiredMixin, ListView):
    model = Test
    context_object_name = "objects"
    template_name = "study/test/list.html"


@method_decorator(not_student, name="dispatch")
class TestEditView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        test = get_object_or_404(Test, pk=pk)
        form = TestForm(instance=test, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Тест изменен!")
        return redirect(reverse("test", kwargs={"pk": pk}))

    def get(self, request, pk, *args, **kwargs):
        test = get_object_or_404(Test, pk=pk)
        form = TestForm(instance=test)

        return render(request, "study/test/edit.html", {
            "form": form,
            "test": test,
        })


@method_decorator(not_student, name="dispatch")
class TestCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = TestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Тест создан!")

        return redirect(reverse("tests"))

    def get(self, request, *args, **kwargs):
        form = TestForm()

        return render(request, "study/test/add.html", {
            "form": form,
        })


@method_decorator(not_student, name="dispatch")
class CheckTestView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        student_try = get_object_or_404(Try, pk=kwargs["pk"])

        student_try.checking(request.POST)

        messages.success(request, "Тест проверен")

        return redirect(reverse("test", kwargs={"pk": student_try.test.pk}))

    def get(self, request, *args, **kwargs):
        student_try = get_object_or_404(Try, pk=kwargs["pk"])

        return render(request, "study/test/check.html", {
            "try": student_try
        })


@not_student
def delete_test(request, pk):

    test = get_object_or_404(Test, pk=pk)
    name = test.name
    test.delete()
    messages.success(request, f"Тест {name} удален!")
    if request.user.profile.type == 1:
        return redirect(reverse("tests"))
    return redirect(reverse("my-tests"))


@method_decorator(not_student, name="dispatch")
class TestQuestionCreateView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        form = QuestionForm(request.POST)

        if form.is_valid():
            new_question = form.save(commit=False)
            new_question.test = get_object_or_404(Test, pk=pk)
            new_question.save()
            messages.success(request, "Вопрос создан!")

            if new_question.type == "TX":
                Answer.objects.create(question=new_question, text="Ответ")

            answer_num = 1
            while True:
                answer = request.POST.get(f"answer-{answer_num}")
                if answer:
                    correct = bool(request.POST.get(f"answer-{answer_num}-correct"))
                    Answer.objects.create(question=new_question, correct=correct, text=answer)
                    answer_num += 1
                    continue
                break

        return redirect(reverse("test", kwargs={"pk": pk}))

    def get(self, request, *args, **kwargs):
        form = QuestionForm()
        return render(request, "study/test/question-add.html", {
            "form": form,
            "types": Question.Type.choices
        })


@not_student
def delete_question(request, test_pk, question_pk):

    question = get_object_or_404(Question, pk=question_pk)
    name = question.text
    question.delete()
    messages.success(request, f"Вопрос {name} удален!")

    return redirect(reverse("test", kwargs={"pk": test_pk}))


@method_decorator(not_student, name="dispatch")
class TestQuestionEditView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        question = get_object_or_404(Question, pk=kwargs["question_pk"])
        form = QuestionForm(instance=question, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Вопрос изменен!")

        return redirect(reverse("test-question", kwargs=kwargs))

    def get(self, request, *args, **kwargs):
        question = get_object_or_404(Question, pk=kwargs["question_pk"])
        form = QuestionForm(instance=question)
        answer_form = AnswerForm()
        return render(request, "study/test/question.html", {
            "form": form,
            "answer_form": answer_form,
            "question": question,
        })


@not_student
def add_answer_variant(request, pk):
    if request.method == "POST":
        question = get_object_or_404(Question, pk=pk)
        form = AnswerForm(request.POST)
        if form.is_valid():
            new_answer = form.save(commit=False)
            new_answer.question = question
            new_answer.save()
            messages.success(request, "Добавлен вариант ответа")

        return redirect(reverse("test-question", kwargs={"question_pk": pk, "test_pk": question.test.pk}))
    else:
        return redirect(reverse("tests"))


@not_student
def add_correct_text_answer(request, pk):
    if request.method == "POST":
        question = get_object_or_404(Question, pk=pk)
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = question.answers.first()
            if answer:
                answer.text = form.cleaned_data.get("text")
                answer.save()
                messages.success(request, "Правильный ответ изменен")
            else:
                new_answer = form.save(commit=False)
                new_answer.question = question
                new_answer.save()
                messages.success(request, "Правильный ответ добавлен")

        return redirect(reverse("test-question", kwargs={"question_pk": pk, "test_pk": question.test.pk}))
    else:
        return redirect(reverse("tests"))


@not_student
def delete_answer(request, pk):

    answer = get_object_or_404(Answer, pk=pk)
    name = answer.text
    answer.delete()
    messages.success(request, f"Ответ {name} удален!")

    return HttpResponse("Answer delete successfully!")


@method_decorator(teacher_only, name="dispatch")
class MyGroupListView(LoginRequiredMixin, ListView):
    model = User
    context_object_name = "groups"
    template_name = "study/teacher/my_group.html"

    def get_queryset(self):
        return {subject.group for subject in TeacherGroupSubject.objects.filter(teacher=self.request.user)}


@method_decorator(teacher_only, name="dispatch")
class MyGroupCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = GroupForm(request.POST)
        if form.is_valid():
            new_group = form.save(commit=False)
            new_group.owner = request.user
            new_group.save()
            messages.success(request, "Ваша группа создана!")
            return redirect(reverse("my-group"))

        return redirect(reverse("my-group-create"))

    def get(self, request, *args, **kwargs):
        form = GroupForm()
        return render(request, "study/teacher/create-group.html", {"form": form})


def exclude_student(request, pk):
    student = get_object_or_404(User, pk=pk)
    group = student.group_set.first()
    group_pk = group.pk
    group.students.remove(student)
    messages.success(request, "Студент был исключен")
    return redirect(reverse("group-students", kwargs={"pk": group_pk}))


@not_student
def add_subject_to_group(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    group = request.user.study_groups.first()
    if not group:
        messages.error(request, "У вас нет группы!")
        return redirect(reverse("my-group"))
    subject.groups.add(group)
    messages.success(request, "Дисциплина добавлена в вашу группу")
    return redirect(reverse("my-group"))


@not_student
def remove_subject_from_group(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    group = request.user.study_groups.first()
    if not group:
        messages.error(request, "У вас нет группы!")
        return redirect(reverse("my-group"))
    subject.groups.remove(group)
    messages.success(request, "Дисциплина удалена из вашей группы")
    return redirect(reverse("my-group"))


@method_decorator(not_student, name="dispatch")
class StudentGradeView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        student = get_object_or_404(User, pk=kwargs.get("pk"))
        grade = student.profile.get_grade()
        print(grade)

        return render(
            request,
            "study/student-grade.html",
            {
                "student": student,
                "grade": grade
            }
        )


@method_decorator(teacher_only, name="dispatch")
class MySubjectsListView(LoginRequiredMixin, ListView):
    model = Subject
    context_object_name = "objects"
    template_name = "study/teacher/my_subjects.html"


@method_decorator(teacher_only, name="dispatch")
class MySubjectCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        subject_name = request.POST.get("name")
        subject = Subject.objects.create(name=subject_name)
        messages.success(request, "Дисциплина создана!")

        return redirect(reverse("my-subject", kwargs={"pk": subject.pk}))

    def get(self, request, *args, **kwargs):
        form = SubjectForm()
        return render(request, "study/teacher/create-subject.html", {"form": form})


@method_decorator(teacher_only, name="dispatch")
class MySubjectEditView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        subject = get_object_or_404(Subject, pk=kwargs["pk"])
        form = SubjectForm(instance=subject, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Дисциплина изменена!")

        return redirect(reverse("my-subject", kwargs=kwargs))

    def get(self, request, *args, **kwargs):
        subject = get_object_or_404(Subject, pk=kwargs["pk"])
        form = SubjectForm(instance=subject)
        group_form = GroupForTeacherSubjectForm()
        groups = Group.objects.all()
        return render(request, "study/teacher/edit-subject.html", {
            "form": form, "group_form": group_form, "subject": subject, "groups": groups,
        })


@method_decorator(teacher_only, name="dispatch")
class MySubjectAddToGroupView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        subject = get_object_or_404(Subject, pk=kwargs["pk"])
        form = GroupForTeacherSubjectForm(request.POST)
        if form.is_valid():
            group = form.cleaned_data.get("group")
            TeacherGroupSubject.objects.get_or_create(
                group=group,
                teacher=request.user,
                subject=subject
            )
            messages.success(request, "Дисциплина добавлена к группе!")

        return redirect(reverse("my-subject", kwargs={"pk": subject.pk}))


@teacher_only
def remove_my_subject_from_group(request, pk):
    subject = get_object_or_404(TeacherGroupSubject, pk=pk)
    subject_pk = subject.subject.pk
    subject.delete()
    messages.success(request, f"Дисциплина удалена из группы!")

    return redirect(reverse("my-subject", kwargs={"pk": subject_pk}))


@method_decorator(teacher_only, name="dispatch")
class MyLessonsListView(LoginRequiredMixin, ListView):
    model = Lesson
    context_object_name = "objects"
    template_name = "study/teacher/my_lessons.html"

    def get_queryset(self):
        lessons = []
        for subject in TeacherGroupSubject.objects.filter(teacher=self.request.user):
            lessons += list(subject.lessons.all())
        return lessons


@method_decorator(teacher_only, name="dispatch")
class MyLessonCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = LessonForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_lesson = form.save()
            photos_field = request.FILES.getlist("photos")
            videos_field = request.FILES.getlist("videos")
            files_field = request.FILES.getlist("files")

            if photos_field:
                for photo in photos_field:
                    LessonPhoto.objects.create(photo=photo, lesson=new_lesson)
            if videos_field:
                for video in videos_field:
                    LessonVideo.objects.create(video=video, lesson=new_lesson)
            if files_field:
                for file in files_field:
                    LessonFile.objects.create(file=file, lesson=new_lesson)

            messages.success(request, "Занятие создано")

        return redirect(reverse("my-lessons"))

    def get(self, request, *args, **kwargs):
        user = request.user
        form = LessonForm()
        tests = Test.objects.filter(lesson__isnull=True)
        subjects = TeacherGroupSubject.objects.filter(teacher=user)
        types = Lesson.type.field.choices
        return render(request, "study/teacher/create-lesson.html", {
            "form": form,
            "tests": tests,
            "subjects": subjects,
            "types": types
        })


@method_decorator(teacher_only, name="dispatch")
class MyLessonEditView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        lesson = get_object_or_404(Lesson, pk=kwargs["pk"])
        form = LessonForm(instance=lesson, data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            photos_field = request.FILES.getlist("photos")
            videos_field = request.FILES.getlist("videos")
            files_field = request.FILES.getlist("files")

            if photos_field:
                for photo in photos_field:
                    LessonPhoto.objects.create(photo=photo, lesson=lesson)
            if videos_field:
                for video in videos_field:
                    LessonVideo.objects.create(video=video, lesson=lesson)
            if files_field:
                for file in files_field:
                    LessonFile.objects.create(file=file, lesson=lesson)

            messages.success(request, "Занятие изменено")

        return redirect(reverse("my-lesson", kwargs=kwargs))

    def get(self, request, *args, **kwargs):
        lesson = get_object_or_404(Lesson, pk=kwargs["pk"])
        user = request.user
        form = LessonForm(instance=lesson)
        tests = Test.objects.filter(lesson__isnull=True)
        subjects = TeacherGroupSubject.objects.filter(teacher=user)
        types = Lesson.type.field.choices
        photos = lesson.photos.all()
        videos = lesson.videos.all()
        files = lesson.files.all()
        return render(request, "study/teacher/edit-lesson.html", {
            "lesson": lesson,
            "form": form,
            "tests": tests,
            "subjects": subjects,
            "types": types,
            "photos": photos,
            "videos": videos,
            "files": files,
        })


class MyTestsListView(TestsListView):
    model = Test
    context_object_name = "objects"
    template_name = "study/test/list.html"

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class StudentSubjectView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        user = self.request.user
        subject = get_object_or_404(TeacherGroupSubject, pk=kwargs["pk"])

        if not user.group_set.first():
            return HttpResponse("No permission")

        if user.group_set.first() != subject.group:
            return HttpResponse("No permission")

        lessons = {l_type[1]: [] for l_type in Lesson.type.field.choices}
        for lesson in subject.lessons.all():
            lessons[lesson.get_type_display()].append(lesson)

        return render(request, "study/student/subject.html", {
            "subject": subject,
            "lessons": lessons,
        })


class StudentLessonView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        user = self.request.user
        lesson = get_object_or_404(Lesson, pk=kwargs["pk"])

        if not user.group_set.first():
            return HttpResponse("No permission")
        if user.group_set.first() != lesson.subject.group:
            return HttpResponse("No permission")

        my_best_try = 0
        if lesson.test:
            my_best_try = lesson.get_test_user_best_try(user)

        work_form, work_score = None, None

        if lesson.type == "IW":
            work_form = StudentWorkForm()
            student_work = StudentIndividualWork.objects.filter(user=user, lesson=lesson).first()
            if student_work:
                work_score = student_work.score or "Проверяется"
            else:
                work_score = None

        return render(request, "study/student/lesson.html", {
            "lesson": lesson,
            "best_try": my_best_try,
            "work_score": work_score,
            "work_form": work_form
        })


class StudentIndividualWorkView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        user = self.request.user
        lesson = get_object_or_404(Lesson, pk=kwargs["pk"])

        if not user.group_set.first():
            return HttpResponse("No permission")
        if user.group_set.first() != lesson.subject.group:
            return HttpResponse("No permission")

        if StudentIndividualWork.objects.filter(user=user, lesson=lesson):
            messages.error(request, "Вы уже отправили работу")
            return redirect(reverse("student-lesson", kwargs=self.kwargs))

        work_form = StudentWorkForm(request.POST, request.FILES)
        if work_form.is_valid():
            work = work_form.save(commit=False)
            work.user = user
            work.lesson = lesson
            work.save()
            messages.success(request, "Работа отправлена на проверку")

        return redirect(reverse("student-lesson", kwargs=self.kwargs))


class StudentTestView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = self.request.user
        test = get_object_or_404(Test, pk=kwargs["pk"])

        if not user.group_set.first():
            return HttpResponse("No permission")

        score, need_check = test.calculate_score(request.POST, user)
        student_try = Try.objects.create(user=user, test=test, score=score, need_check=need_check)
        for student_answer in StudentAnswer.objects.filter(user=user, question__test=test, student_try__isnull=True):
            student_answer.student_try = student_try
            student_answer.save()

        if need_check:
            messages.success(request, f"Ваш тест отправлен на проверку")
        else:
            messages.success(request, f"Ваш балл составил {score}")

        return redirect(reverse("student-lesson", kwargs={"pk": test.lesson.pk}))

    def get(self, request, *args, **kwargs):
        user = self.request.user
        test = get_object_or_404(Test, pk=kwargs["pk"])

        if not user.group_set.first():
            return HttpResponse("No permission")

        if test.lesson.is_late():
            messages.error(request, "Возможности сдать тест больше нет!")
            return redirect(reverse("student-lesson", kwargs={"pk": test.lesson.pk}))

        return render(request, "study/student/test.html", {
            "test": test,
        })


@not_student
def download_test_tries(request, test_id):
    test = get_object_or_404(Test, pk=test_id)
    queryset = Try.objects.filter(test=test)
    data = [{"студент": instance.user.username, "балл": instance.score} for instance in queryset]

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/xlsx')
    response['Content-Disposition'] = f'attachment; filename="{test.name}_{str(dt.now())}.xlsx"'

    with pd.ExcelWriter(response) as writer:
        df.to_excel(writer, sheet_name=f'Результаты теста {test.name}')

    return response


class UploadSubjectsView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        form = ExcelForm(request.POST, request.FILES)
        if form.is_valid():
            df = pd.read_excel(request.FILES['excel'], names=["name", "teacher", "group"])
            first_iter = True
            for index, row in df.iterrows():
                if first_iter:
                    first_iter = False
                    continue
                name = row["name"]
                teacher = User.objects.filter(username=row["teacher"]).first()
                group = Group.objects.filter(number=row["group"]).first()
                if not(pd.isna(name)) and teacher and group:
                    subject = Subject.objects.get_or_create(name=name)
                    TeacherGroupSubject.objects.get_or_create(teacher=teacher, subject=subject[0], group=group)
                elif not(pd.isna(name)):
                    Subject.objects.get_or_create(name=name)
            messages.success(request, "Дисциплины успешно загружены")

        if request.user.profile.type == 1:
            return redirect(reverse("subjects"))
        return redirect(reverse("my-subjects"))

    def get(self, request, *args, **kwargs):
        form = ExcelForm()
        return render(request, "study/subjects/upload.html", {"form": form})


class UploadLessonsView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        form = ExcelForm(request.POST, request.FILES)
        if form.is_valid():
            df = pd.read_excel(request.FILES['excel'], names=["name", "type", "subject", "teacher", "group", "text"])
            first_iter = True
            for index, row in df.iterrows():
                if first_iter:
                    first_iter = False
                    continue

                subject = Subject.objects.filter(name=row["subject"]).first()
                teacher = User.objects.filter(username=row["teacher"]).first()
                group = Group.objects.filter(number=row["group"]).first()
                subject = TeacherGroupSubject.objects.filter(teacher=teacher, subject=subject, group=group).first()
                name = None if pd.isna(row["name"]) else row["name"]
                text = None if pd.isna(row["text"]) else row["text"]
                l_type = None if pd.isna(row["type"]) else row["type"]

                if name and l_type and subject:
                    Lesson.objects.get_or_create(name=name, text=text, subject=subject, type=l_type)

            messages.success(request, "Занятия успешно загружены")

        if request.user.profile.type == 1:
            return redirect(reverse("lessons"))
        return redirect(reverse("my-lessons"))

    def get(self, request, *args, **kwargs):
        form = ExcelForm()
        return render(request, "study/lesson/upload.html", {"form": form})


def about(request):
    return render(request, "study/about.html")
