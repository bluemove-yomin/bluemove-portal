from django.urls import path
from .views import *

app_name = "applynsubmit"
urlpatterns = [
    path("applymembership", applymembership, name="applymembership"),
    path(
        "applymembershipwithdrawal",
        applymembershipwithdrawal,
        name="applymembershipwithdrawal",
    ),
    path(
        "applymembership/cron-delete-all-expired-recruiting-data",
        cron_delete_all_expired_recruiting_data,
        name="cron_delete_all_expired_recruiting_data",
    ),
    path(
        "applymembershipwithdrawal/cron-delete-delete-queued-alumni-data",
        cron_delete_delete_queued_alumni_data,
        name="cron_delete_delete_queued_alumni_data",
    ),
]
