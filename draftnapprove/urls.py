from django.urls import path
from .views import *

app_name = "draftnapprove"
urlpatterns = [
    path("activityreport", activityreport, name="activityreport"),
    path("activityreport/cron-remind-approvers-about-all-activity-reports-in-the-queue", cron_remind_approvers_about_all_activity_reports_in_the_queue, name="cron_remind_approvers_about_all_activity_reports_in_the_queue"),
    path("activityreport/cron-notify-about-tasks-to-be-done", cron_notify_about_tasks_to_be_done, name="cron_remind_approvers_about_all_activity_reports_in_the_queue"),
]
