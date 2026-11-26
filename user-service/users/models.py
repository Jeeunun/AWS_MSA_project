from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # ✅ AbstractUser가 기본으로 제공하는 first_name/last_name 제거
    first_name = None
    last_name = None

    # ✅ 단일 이름 필드만 사용
    name = models.CharField(max_length=150, blank=True)

    token_id = models.IntegerField(null=True, blank=True)
    tel = models.CharField(max_length=20, null=True, blank=True)
    birth = models.CharField(max_length=10, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    team = models.CharField(max_length=20, null=True, blank=True)

    # ✅ Cognito 동기화 상태
    COGNITO_STATUS_CHOICES = [
        ("active", "Active"),
        ("disabled", "Disabled"),
        ("deleted", "Deleted"),
        ("unknown", "Unknown"),
    ]
    cognito_status = models.CharField(
        max_length=16, choices=COGNITO_STATUS_CHOICES, default="active"
    )
    cognito_deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name or self.username


class LegacyUser(models.Model):
    idx = models.BigAutoField(primary_key=True)
    token_id = models.IntegerField()
    id = models.CharField(max_length=10)
    pw = models.CharField(max_length=10)
    email = models.CharField(max_length=20)
    tel = models.SmallIntegerField()
    birth = models.SmallIntegerField()
    gender = models.IntegerField()
    team = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user'


