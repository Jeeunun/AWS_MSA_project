from rest_framework import serializers
from .models import Schedule, Predict, Coupon, TotalRank, AttackRank, DefenseRank

class ScheduleSerializer(serializers.ModelSerializer):
    """경기 일정/결과 시리얼라이저"""
    winner = serializers.SerializerMethodField()
    
    def get_winner(self, obj):
        # 경기가 끝났고 winner 값이 있는 경우
        if obj.gameStatus == 'END' and obj.winner:
            return obj.winner.lower()
        # 경기 전이거나 결과가 없으면 None
        return None
    
    class Meta:
        model = Schedule
        fields = [
            'idx', 'match_date', 'startTime', 'awayTeamName', 'awayResult',
            'homeTeamName', 'homeResult', 'gameStatus', 'fieldname', 'winner',
            'created_at', 'updated_at'
        ]

class PredictSerializer(serializers.ModelSerializer):
    """예측 시리얼라이저"""
    schedule = ScheduleSerializer(read_only=True)
    
    class Meta:
        model = Predict
        fields = ['idx', 'schedule', 'user_id', 'predicted', 'created_at', 'updated_at']

class PredictCreateSerializer(serializers.ModelSerializer):
    """예측 생성 시리얼라이저"""
    class Meta:
        model = Predict
        fields = ['predicted']

class CouponSerializer(serializers.ModelSerializer):
    """쿠폰 시리얼라이저"""
    predict = PredictSerializer(read_only=True)
    
    class Meta:
        model = Coupon
        fields = [
            'idx', 'predict', 'code', 'coupon_status',
            'created_at', 'updated_at', 'expire_at'
        ]

class TotalRankSerializer(serializers.ModelSerializer):
    """종합 순위 시리얼라이저"""
    class Meta:
        model = TotalRank
        fields = [
            'idx', 'rank', 'team', 'game', 'win', 'draw', 'loss', 
            'wpct', 'gb', 'streak'
        ]

class AttackRankSerializer(serializers.ModelSerializer):
    """공격 순위 시리얼라이저"""
    class Meta:
        model = AttackRank
        fields = [
            'idx', 'rank', 'team', 'batAb', 'batH', 'bat2b', 'bat3b', 
            'batHr', 'batRbi', 'batR', 'batSb', 'batBbhp', 'batSo', 
            'batGdp', 'batAvg', 'batObp', 'batSlg', 'batOps'
        ]

class DefenseRankSerializer(serializers.ModelSerializer):
    """수비 순위 시리얼라이저"""
    class Meta:
        model = DefenseRank
        fields = [
            'idx', 'rank', 'team', 'pitIp', 'pitH', 'pitHr', 'pitR', 
            'pitEr', 'pitBbhp', 'pitSo', 'pitEra', 'fldErr', 'pitWhip', 
            'pitQs', 'pitHld', 'pitSv'
        ]
