from django.urls import path

from . import views

urlpatterns = [
    path("", view=views.TaskListCreateView.as_view(), name="task-list-create"),
]