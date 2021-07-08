from django.urls import path
from .views import *

app_name = 'member'
urlpatterns = [
    path('myaccount', myaccount, name='myaccount'),
]