from django.urls import path
from .views import *

app_name = 'applynsubmit'
urlpatterns = [
    path('applymembership', applymembership, name='applymembership'),
]