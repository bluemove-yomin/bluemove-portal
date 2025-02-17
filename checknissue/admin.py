from django.contrib import admin
from .models import *


@admin.register(Issuecert)
class IssuecertAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "birthday",
        "email_host",
        "created_at",
    )
    search_fields = (
        "code",
        "birthday",
        "email_host",
        "created_at",
    )
