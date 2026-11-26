from django.db import models
from django.utils import timezone
# Create your models here.
# class Result(models.Model):
#     team1 = models.CharField(max_length=5, null=False)
#     team1_score = models.PositiveSmallIntegerField(null=True, blank=True)

#     team2 = models.CharField(max_length=5, null=False)
#     team2_score = models.PositiveSmallIntegerField(null=True, blank=True)

#     time = models.CharField(max_length=20, null=False)  # 시간 문자열로 저장
#     status = models.CharField(max_length=5, null=False)  # 경기전/종료 등

#     win = models.CharField(max_length=5, null=True, blank=True)
#     def __str__(self):
#         return f"{self.team1} vs {self.team2} ({self.status})"


class Result(models.Model):
    date = models.DateTimeField(default=timezone.now)
    start_time = models.CharField(max_length=5,null=True, blank=True)
    away_team = models.CharField(max_length=5)
    at_score = models.PositiveSmallIntegerField(null=True, blank=True)
    home_team = models.CharField(max_length=5)
    ht_score = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=5)
    stadium = models.CharField(max_length=30, null=True, blank=True)
    winner = models.CharField(max_length=5, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'event_result'

# events/models.py
from django.db import models
from django.utils import timezone

class Result(models.Model):
    date = models.DateTimeField(default=timezone.now)
    start_time = models.CharField(max_length=5, null=True, blank=True)
    away_team = models.CharField(max_length=5)
    at_score = models.PositiveSmallIntegerField(null=True, blank=True)
    home_team = models.CharField(max_length=5)
    ht_score = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=5)  # 예: 경기전/종료/경기취소
    stadium = models.CharField(max_length=30, null=True, blank=True)
    winner = models.CharField(max_length=5, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "event_result"

    def __str__(self):
        return f"{self.date:%Y-%m-%d %H:%M} {self.away_team} @ {self.home_team}"


class Predict(models.Model):
    """사용자 예측 (사용자 토큰 기준)"""
    idx = models.BigAutoField(primary_key=True)
    token_id = models.IntegerField()                   # ERD: int
    date = models.DateTimeField(default=timezone.now)  # 예측 시각
    predicted = models.CharField(max_length=10)        # 'AWAY' or 'HOME'
    result = models.ForeignKey(Result, on_delete=models.CASCADE, db_column="idx2", related_name="predictions")

    class Meta:
        db_table = "predict"
        constraints = [
            # 같은 사용자가 같은 경기(result)에는 한 번만 참여
            models.UniqueConstraint(fields=["token_id", "result"], name="uniq_token_result"),
        ]


class Coupon(models.Model):
    """쿠폰 (예측 시 발급 연결)"""
    idx = models.BigAutoField(primary_key=True)
    token_id = models.IntegerField()
    code = models.CharField(max_length=100, unique=True)
    status = models.PositiveSmallIntegerField(default=0)  # 0=미사용, 1=사용
    expire_at = models.DateTimeField()
    predict = models.OneToOneField(Predict, on_delete=models.CASCADE, db_column="idx2", related_name="coupon")

    class Meta:
        db_table = "coupon"
        indexes = [models.Index(fields=["token_id", "status"])]


class TotalRank(models.Model):
    rank = models.SmallIntegerField()
    team = models.CharField(max_length=5)
    games = models.SmallIntegerField(null=True)
    wins = models.SmallIntegerField(null=True)
    lose = models.SmallIntegerField(null=True)
    rate = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    gb = models.DecimalField(max_digits=5, decimal_places=1, null=True)
    streak = models.CharField(max_length=5, null=True)

class AttackRank(models.Model):
    rank = models.SmallIntegerField()
    team = models.CharField(max_length=5)
    at_bats = models.SmallIntegerField(null=True)
    hits = models.SmallIntegerField(null=True)
    doubles = models.SmallIntegerField(null=True)
    triples = models.SmallIntegerField(null=True)
    home_runs = models.SmallIntegerField(null=True)
    rbi = models.SmallIntegerField(null=True)
    runs_scored = models.SmallIntegerField(null=True)
    stolen_bases = models.SmallIntegerField(null=True)
    walks_hit_by_pitch = models.SmallIntegerField(null=True)
    strikeouts = models.SmallIntegerField(null=True)
    double_plays = models.SmallIntegerField(null=True)
    batting_avg = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    obp = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    slg = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    ops = models.DecimalField(max_digits=5, decimal_places=3, null=True)


class DefendRank(models.Model):
    rank = models.SmallIntegerField()
    team = models.CharField(max_length=5)
    innings = models.CharField(max_length=10, null=True)
    hits_allowed = models.SmallIntegerField(null=True)
    home_runs_allowed = models.SmallIntegerField(null=True)
    runs_allowed = models.SmallIntegerField(null=True)
    earned_runs = models.SmallIntegerField(null=True)
    walks_hit_by_pitch = models.SmallIntegerField(null=True)
    strikeouts = models.SmallIntegerField(null=True)
    errors = models.SmallIntegerField(null=True)
    whip = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    qs = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    saves = models.SmallIntegerField(null=True)