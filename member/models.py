from django.db import models

# models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, null=True)

    class Meta:
        verbose_name = "휴대전화 번호"
        verbose_name_plural = "휴대전화 번호(들)"
