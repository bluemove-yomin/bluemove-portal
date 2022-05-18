from django.db import models

# models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, null=True)

    class Meta:
        verbose_name = "휴대전화 번호"
        verbose_name_plural = "휴대전화 번호(들)"


class Signupvcode(models.Model):
    last_name = models.CharField(max_length=4, null=False)
    phone_last_five_digits = models.CharField(max_length=5, null=False)
    code = models.CharField(max_length=6, null=False)
    will_expire_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "인증 번호"
        verbose_name_plural = "인증 번호(들)"
