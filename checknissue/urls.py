from django.urls import path
from .views import *

app_name = 'checknissue'
urlpatterns = [
    path('checklist', checklist, name='checklist'),
    path('checkcert', checkcert, name='checkcert'),
    path('issuecert', issuecert, name='issuecert'),
]