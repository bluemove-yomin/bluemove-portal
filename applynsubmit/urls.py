from django.urls import path
from .views import *

app_name = "applynsubmit"
urlpatterns = [
    path("applymembership", applymembership, name="applymembership"),
    path("<str:wanted_id>/cron_delete_all_recruiting_data", cron_delete_all_recruiting_data, name="cron_delete_all_recruiting_data"),
]
