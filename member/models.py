from django.db import models

# models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, null=True)

    class Meta:
        verbose_name = "휴대전화 번호"
        verbose_name_plural = "휴대전화 번호(들)"


class Vcode(models.Model):
    last_name = models.CharField(max_length=4, null=False)
    phone_last_five_digits = models.CharField(max_length=5, null=True)
    email_last_letter_with_host = models.CharField(max_length=20, null=True)
    code = models.CharField(max_length=10, null=False)
    will_expire_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "휴대전화 번호 인증 번호 또는 이메일 인증 코드"
        verbose_name_plural = "휴대전화 번호 인증 번호 또는 이메일 인증 코드(들)"
