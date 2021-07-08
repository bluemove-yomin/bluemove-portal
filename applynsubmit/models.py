from django.db import models

# models
from django.contrib.auth.models import User


class Applymembership(models.Model):
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    wanted_id = models.CharField(max_length=36, null=True, blank=True)
    wanted_title = models.CharField(max_length=50, null=True, blank=True)
    self_intro = models.TextField(max_length=260, null=True, blank=True)
    self_intro_len = models.IntegerField(default=0, null=True, blank=True)
    reason = models.TextField(max_length=260, null=True, blank=True)
    reason_len = models.IntegerField(default=0, null=True, blank=True)
    plan = models.TextField(max_length=260, null=True, blank=True)
    plan_len = models.IntegerField(default=0, null=True, blank=True)
    tracking = models.CharField(max_length=20, null=True, blank=True)
    tracking_reference = models.CharField(max_length=10, null=True, blank=True)
    tracking_etc = models.CharField(max_length=100, null=True, blank=True)
    portfolio = models.CharField(max_length=100, null=True, blank=True)
    last_saved = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    pf = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        choices={
            ("미결정", "미결정"),
            ("선발", "선발"),
            ("미선발", "미선발"),
        },
        default="미결정",
    )
    notified = models.BooleanField(default=False)
    joined = models.BooleanField(default=False)
    received_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    will_be_deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "지원서"
        verbose_name_plural = "지원서(들)"


class ApplymembershipNoti(models.Model):
    saved_by = models.ForeignKey(User, on_delete=models.CASCADE)
    wanted_id = models.CharField(max_length=36, null=True, blank=True)
    wanted_title = models.CharField(max_length=50, null=True, blank=True)
    title = models.CharField(max_length=50, null=True, blank=True)
    passed_content = models.TextField(max_length=510, null=True, blank=True)
    failed_content = models.TextField(max_length=510, null=True, blank=True)
    sent = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    will_be_deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "통보 메일"
        verbose_name_plural = "통보 메일(들)"