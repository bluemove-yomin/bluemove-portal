from django.contrib import admin
from .models import *


@admin.register(Applymembership)
class ApplymembershipAdmin(admin.ModelAdmin):
    list_display = (
        "wanted_id",
        "wanted_title",
        "applicant",
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
        "will_be_deleted_on",
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
        "will_be_deleted_on",
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
        "will_be_deleted_on",
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
        "will_be_deleted_on",
    )


@admin.register(Applymembershipwithdrawal)
class ApplymembershipwithdrawalAdmin(admin.ModelAdmin):
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


@admin.register(ApplymembershipwithdrawalQueue)
class ApplymembershipwithdrawalQueueAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "period",
        "name",
        "email",
        "role",
        "activities",
        "data_boolean",
        "reason",
        "row_idx",
        "slack_ts",
        "added_at",
        "will_be_deleted_on",
    )
    search_fields = (
        "number",
        "period",
        "name",
        "email",
        "role",
        "activities",
        "data_boolean",
        "reason",
        "row_idx",
        "slack_ts",
        "added_at",
        "will_be_deleted_on",
    )