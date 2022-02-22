from django.db import models

# models
from django.contrib.auth.models import User


class Applymembership(models.Model):
    wanted_id = models.CharField(max_length=36, null=True, blank=True)
    wanted_title = models.CharField(max_length=50, null=True, blank=True)
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
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
    wanted_id = models.CharField(max_length=36, null=True, blank=True)
    wanted_title = models.CharField(max_length=50, null=True, blank=True)
    saved_by = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50, null=True, blank=True)
    passed_content = models.TextField(max_length=510, null=True, blank=True)
    failed_content = models.TextField(max_length=510, null=True, blank=True)
    sent = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    will_be_deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "통보 메일"
        verbose_name_plural = "통보 메일(들)"


class Applymembershipwithdrawal(models.Model):
    birthday = models.CharField(max_length=4)
    phone_last = models.CharField(max_length=4)
    email_host = models.CharField(max_length=20)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "인증 코드"
        verbose_name_plural = "인증 코드(들)"


class ApplymembershipwithdrawalQueue(models.Model):
    number = models.CharField(max_length=50)
    period = models.CharField(max_length=100)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    activities = models.CharField(max_length=300)
    data_boolean = models.BooleanField(default=False)
    reason = models.CharField(max_length=50)
    row_idx = models.CharField(max_length=10)
    slack_ts = models.CharField(max_length=100)
    added_at = models.DateTimeField(null=True, blank=True)
    will_be_deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "탈퇴 신청자"
        verbose_name_plural = "탈퇴 신청자(들)"
