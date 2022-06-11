from django.urls import path
from .views import *

app_name = "member"
urlpatterns = [
    path("phone-num-validation", phone_num_validation, name="phone_num_validation"),
    path("email-addr-validation", email_addr_validation, name="email_addr_validation"),
    path("kor-name-romanizer", kor_name_romanizer, name="kor_name_romanizer"),
    path("myaccount", myaccount, name="myaccount"),
    path(
        "cron-delete-all-expired-v-codes",
        cron_delete_all_expired_v_codes,
        name="cron_delete_all_expired_v_codes",
    ),
    path(
        "cron-delete-all-inactive-users",
        cron_delete_all_inactive_users,
        name="cron_delete_all_inactive_users",
    ),
]
