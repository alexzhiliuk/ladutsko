from django.urls import path
from study.api import views as api_views
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('v1/subject-create/', api_views.SubjectCreateView.as_view()),
    path('v1/subject-edit/<int:pk>/', api_views.SubjectEditView.as_view()),
    path('v1/test-create/', api_views.TestCreateView.as_view()),
    path('v1/test-edit/<int:pk>/', api_views.TestEditView.as_view()),
    path('v1/test-question-add/<int:pk>/', api_views.TestQuestionCreateView.as_view()),
]