from django.db import models

class Team(models.Model):
    """팀 정보 테이블"""
    team_id = models.AutoField(primary_key=True)
    team_name = models.CharField(max_length=20, unique=True, verbose_name="팀명", default='', blank=True)
    team_code = models.CharField(max_length=4, unique=True, verbose_name="팀코드", default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, null=True, verbose_name="수정일")

    class Meta:
        db_table = 'kbo_team'
        verbose_name = '팀'
        verbose_name_plural = '팀들'

    def __str__(self) -> str:
        return f"{self.team_name}({self.team_code})"

class Player(models.Model):
    """선수 정보 테이블"""
    idx = models.BigAutoField(primary_key=True, verbose_name="정보 PK")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, db_column='team_id', verbose_name="팀 PK", related_name='players')
    p_name = models.CharField(max_length=10, verbose_name="선수이름", default='', blank=True)
    p_number = models.SmallIntegerField(verbose_name="등번호", default=0)
    p_position = models.CharField(max_length=5, verbose_name="포지션", default='', blank=True)
    height_cm = models.CharField(max_length=5, verbose_name="키", default='', blank=True)
    weight_kg = models.CharField(max_length=10, verbose_name="몸무게", default='', blank=True)
    birth = models.DateField(verbose_name="생년월일", null=True, blank=True)
    p_info = models.CharField(max_length=10, verbose_name="투타정보", default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, null=True, verbose_name="수정일")

    class Meta:
        db_table = 'kbo_player'
        verbose_name = '선수'
        verbose_name_plural = '선수들'
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'p_number', 'p_name'],
                name='unique_player_by_team_number_name'
            )
        ]

    def __str__(self) -> str:
        return f"{self.p_name}({self.p_number}번)"

class Manager(models.Model):
    """감독 정보 테이블"""
    manager_id = models.AutoField(primary_key=True)
    team = models.OneToOneField(Team, on_delete=models.CASCADE, db_column='team_id', verbose_name="팀 PK", related_name='manager')
    m_name = models.CharField(max_length=20, verbose_name="감독이름", default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, null=True, verbose_name="수정일")

    class Meta:
        db_table = 'kbo_manager'
        verbose_name = '감독'
        verbose_name_plural = '감독들'

    def __str__(self) -> str:
        return f"{self.m_name}({self.team.team_name})"