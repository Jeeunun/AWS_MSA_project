from django.db import models
from django.utils import timezone


class Schedule(models.Model):
    idx = models.BigAutoField(primary_key=True)
    match_date = models.DateField(default=timezone.localdate)
    startTime = models.CharField(max_length=5, null=True, blank=True)
    awayTeamName = models.CharField(max_length=10)
    awayResult = models.PositiveSmallIntegerField(null=True, blank=True)
    homeTeamName = models.CharField(max_length=10)
    homeResult = models.PositiveSmallIntegerField(null=True, blank=True)
    gameStatus = models.CharField(max_length=10, default='BEFORE') 
    fieldname = models.CharField(max_length=30, null=True, blank=True)
    winner = models.CharField(max_length=5, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "event_schedule"
        indexes = [
            models.Index(fields=["match_date"]),
            models.Index(fields=["awayTeamName"]),
            models.Index(fields=["homeTeamName"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["match_date", "startTime", "awayTeamName", "homeTeamName"],
                name="uniq_result_match",
            )
        ]       # unique 키 추가.

    def __str__(self):
        return f"{self.match_date:%Y-%m-%d} {self.startTime or ''} {self.awayTeamName} @ {self.homeTeamName}"


class Predict(models.Model):
    idx = models.BigAutoField(primary_key=True, db_column='idx')
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        db_column="schedule_id",    
        related_name="predictions",
    )
    user_id = models.CharField(max_length=20)  # 로그인 시 입력한 사용자 ID
    predicted = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "event_predict"
        constraints = [
            models.UniqueConstraint(fields=["user_id", "schedule"], name="uniq_token_result"),
        ]



class Coupon(models.Model):
    """쿠폰 (예측 시 발급 연결)"""
    idx = models.BigAutoField(primary_key=True, db_column='idx')
    predict = models.OneToOneField(
        Predict,
        on_delete=models.CASCADE,
        db_column="predict_id",     # DB 컬럼명 유지
        related_name="coupon",
   )
    code = models.CharField(max_length=100, unique=True)
    coupon_status = models.PositiveSmallIntegerField(default=0)  # 0=만료, 1=사용 2=미사용
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expire_at = models.DateTimeField()

    class Meta:
        db_table = "event_coupon"
        indexes = [models.Index(fields=["predict_id"]),
                   models.Index(fields=["coupon_status"]),
                   models.Index(fields=["expire_at"]),]

class Season(models.Model):
    idx = models.AutoField(primary_key=True, db_column='idx')
    season = models.SmallIntegerField()
    startDate = models.DateField()
    endDate = models.DateField()

    class Meta:
        db_table = "event_season"
        constraints = [
            models.UniqueConstraint(fields=['season'], name='uniq_season')
        ]

class TotalRank(models.Model):
    idx = models.BigAutoField(primary_key=True, db_column='idx')
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        db_column="season_id",
        related_name="totalrank"
    )
    rank = models.SmallIntegerField(default=999)
    team = models.CharField(max_length=5)
    game = models.SmallIntegerField(null=True)
    win = models.SmallIntegerField(null=True)
    draw = models.SmallIntegerField(null=True)
    loss = models.SmallIntegerField(null=True)
    wpct = models.DecimalField(max_digits=5, decimal_places=4, null=True)
    gb = models.DecimalField(max_digits=4, decimal_places=1, null=True)
    streak = models.CharField(max_length=5, null=True)

    class Meta:
        db_table = "event_totalrank"

class AttackRank(models.Model):
    idx = models.BigAutoField(primary_key=True, db_column='idx')
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        db_column="season_id",
        related_name="attackrank"
    )
    rank = models.SmallIntegerField(default=999)
    team = models.CharField(max_length=5)
    batAb = models.SmallIntegerField(null=True)
    batH = models.SmallIntegerField(null=True)
    bat2b = models.SmallIntegerField(null=True)
    bat3b = models.SmallIntegerField(null=True)
    batHr = models.SmallIntegerField(null=True)
    batRbi = models.SmallIntegerField(null=True)
    batR = models.SmallIntegerField(null=True)
    batSb = models.SmallIntegerField(null=True)
    batBbhp = models.SmallIntegerField(null=True)
    batSo = models.SmallIntegerField(null=True)
    batGdp = models.SmallIntegerField(null=True)
    batAvg = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    batObp = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    batSlg = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    batOps = models.DecimalField(max_digits=5, decimal_places=3, null=True)

    class Meta:
        db_table = "event_attackrank"

class DefenseRank(models.Model):
    idx = models.BigAutoField(primary_key=True, db_column='idx')
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        db_column="season_id",
        related_name="defenserank"
    )
    rank = models.SmallIntegerField(default=999)
    team = models.CharField(max_length=5)
    pitIp = models.CharField(max_length=10, null=True)
    pitH = models.SmallIntegerField(null=True)
    pitHr = models.SmallIntegerField(null=True)
    pitR = models.SmallIntegerField(null=True)
    pitEr = models.SmallIntegerField(null=True)
    pitBbhp = models.SmallIntegerField(null=True)
    pitSo = models.SmallIntegerField(null=True)
    pitEra = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    fldErr = models.SmallIntegerField(null=True)
    pitWhip = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    pitQs = models.SmallIntegerField(null=True)
    pitHld = models.SmallIntegerField(null=True)
    pitSv = models.SmallIntegerField(null=True)

    class Meta:
        db_table = "event_defenserank"
