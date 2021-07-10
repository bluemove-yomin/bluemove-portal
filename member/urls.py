from django.urls import path
from .views import *

app_name = "member"
urlpatterns = [
    path("myaccount", myaccount, name="myaccount"),
    path(
        "cron-delete-all-inactive-users",
        cron_delete_all_inactive_users,
        name="cron_delete_all_inactive_users",
    ),
]
