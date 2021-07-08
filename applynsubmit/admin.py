from django.contrib import admin
from .models import *


@admin.register(Applymembership)
class ApplymembershipAdmin(admin.ModelAdmin):
    list_display = (
        "wanted_id",
        "wanted_title",
        "applicant",
        "self_intro",
        "reason",
        "plan",
        "tracking",
        "tracking_reference",
        "tracking_etc",
        "portfolio",
        "received",
        "pf",
        "notified",
        "joined",
        "received_at",
        "created_at",
        "updated_at",
        "will_be_deleted_at",
    )
    search_fields = (
        "wanted_id",
        "wanted_title",
        "applicant",
        "self_intro",
        "reason",
        "plan",
        "tracking",
        "tracking_reference",
        "tracking_etc",
        "portfolio",
        "received",
        "pf",
        "notified",
        "joined",
        "received_at",
        "created_at",
        "updated_at",
        "will_be_deleted_at",
    )


@admin.register(ApplymembershipNoti)
class ApplymembershipnotiAdmin(admin.ModelAdmin):
    list_display = (
        "wanted_id",
        "wanted_title",
        "saved_by",
        "title",
        "passed_content",
        "failed_content",
        "sent",
        "updated_at",
        "will_be_deleted_at",
    )
    search_fields = (
        "wanted_id",
        "wanted_title",
        "saved_by",
        "title",
        "passed_content",
        "failed_content",
        "sent",
        "updated_at",
        "will_be_deleted_at",
    )
