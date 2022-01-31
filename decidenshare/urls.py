from django.urls import path
from .views import *

app_name = "decidenshare"
urlpatterns = [
    path("sharebmlink", sharebmlink, name="sharebmlink"),
]
