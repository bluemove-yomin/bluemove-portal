from django.urls import path
from .views import *

app_name = "draftnapprove"
urlpatterns = [
    path("activityreport", activityreport, name="activityreport"),
    path("activityreport/cron-remind-approvers-about-all-activity-reports-in-the-queue", cron_remind_approvers_about_all_activity_reports_in_the_queue, name="cron_remind_approvers_about_all_activity_reports_in_the_queue"),
    path("activityreport/cron-notify-about-tasks-done", cron_notify_about_tasks_done, name="cron_notify_about_tasks_done"),
    path("activityreport/cron-notify-about-tasks-to-be-done", cron_notify_about_tasks_to_be_done, name="cron_notify_about_tasks_to_be_done"),
    path("activityreport/cron-notify-about-msg", cron_notify_about_msg, name="cron_notify_about_msg"),
    path("activityreport/get-google-token/", get_google_token, name="get_google_token"),
]
