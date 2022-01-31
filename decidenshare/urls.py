from django.urls import path
from .views import *

app_name = "decidenshare"
urlpatterns = [
    path("sharebmlink", sharebmlink, name="sharebmlink"),
    path("sharebmlink/cron-delete-all-expired-bmlinks", cron_delete_all_expired_bmlinks, name="cron_delete_all_expired_bmlinks"),
]
