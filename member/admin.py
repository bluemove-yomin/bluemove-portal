from django.contrib import admin

# models
from .models import *

@admin.register(Profile)
class UserAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "phone",
    )

    list_display_links = (
        "user",
        "phone",
    )