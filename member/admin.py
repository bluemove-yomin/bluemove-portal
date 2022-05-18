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
    search_fields = (
        "user",
        "phone",
    )


@admin.register(Signupvcode)
class SignupvcodeAdmin(admin.ModelAdmin):
    list_display = (
        "last_name",
        "phone_last_five_digits",
        "code",
        "will_expire_on",
    )
    list_display_links = (
        "last_name",
        "phone_last_five_digits",
        "code",
        "will_expire_on",
    )
    search_fields = (
        "last_name",
        "phone_last_five_digits",
        "code",
        "will_expire_on",
    )
