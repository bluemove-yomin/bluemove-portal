from django.urls import path
from .views import *

app_name = "draftnapprove"
urlpatterns = [
    path("activityreport", activityreport, name="activityreport"),
]
