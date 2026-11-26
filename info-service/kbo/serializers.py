from rest_framework import serializers
from .models import Team, Player, Manager

class TeamSerializer(serializers.ModelSerializer):
    """팀 정보 시리얼라이저"""
    class Meta:
        model = Team
        fields = ['team_id', 'team_name', 'team_code', 'created_at', 'updated_at']

class ManagerSerializer(serializers.ModelSerializer):
    """감독 정보 시리얼라이저"""
    team_name = serializers.CharField(source='team.team_name', read_only=True)
    
    class Meta:
        model = Manager
        fields = ['manager_id', 'm_name', 'team_name', 'created_at', 'updated_at']

class PlayerSerializer(serializers.ModelSerializer):
    """선수 정보 시리얼라이저"""
    team_name = serializers.CharField(source='team.team_name', read_only=True)
    team_code = serializers.CharField(source='team.team_code', read_only=True)
    
    class Meta:
        model = Player
        fields = [
            'idx', 'p_name', 'p_number', 'p_position', 'height_cm', 
            'weight_kg', 'birth', 'p_info', 'team_name', 'team_code',
            'created_at', 'updated_at'
        ]

class TeamDetailSerializer(serializers.ModelSerializer):
    """팀 상세 정보 시리얼라이저 (감독과 선수 포함)"""
    manager = ManagerSerializer(read_only=True)
    players = PlayerSerializer(many=True, read_only=True)
    player_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ['team_id', 'team_name', 'team_code', 'manager', 'players', 'player_count', 'created_at', 'updated_at']
    
    def get_player_count(self, obj):
        return obj.players.count()

class TeamListSerializer(serializers.ModelSerializer):
    """팀 목록 시리얼라이저 (간단한 정보만)"""
    manager_name = serializers.SerializerMethodField()
    player_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ['team_id', 'team_name', 'team_code', 'manager_name', 'player_count']
    
    def get_manager_name(self, obj):
        try:
            return obj.manager.m_name
        except:
            return '미정'
    
    def get_player_count(self, obj):
        return obj.players.count()

