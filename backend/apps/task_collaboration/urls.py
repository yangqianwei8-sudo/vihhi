from django.urls import path

from . import views_pages

app_name = "task_collaboration"

urlpatterns = [
    path("board/", views_pages.task_board, name="task_board"),
    path("workspace/", views_pages.collaboration_workspace, name="workspace"),
    path("process/", views_pages.process_engine, name="process_engine"),
    path("timesheet/", views_pages.timesheet, name="timesheet"),
    path("messages/", views_pages.message_center, name="message_center"),
]

