from django.db import models


class Issuecert(models.Model):
    birthday = models.CharField(max_length=4)
    phone_last = models.CharField(max_length=4)
    email_host = models.CharField(max_length=20)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
            verbose_name = "인증 코드"
            verbose_name_plural = "인증 코드(들)"