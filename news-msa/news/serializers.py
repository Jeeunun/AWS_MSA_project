from rest_framework import serializers
from .models import News

class NewsSerializer(serializers.ModelSerializer):
    """뉴스 시리얼라이저"""
    class Meta:
        model = News
        fields = [
            'id', 'title', 'keyword', 'link', 
            'crawl_date', 'created_at'
        ]
    
    def to_representation(self, instance):
        """JSON 응답 시 추가 정보 포함"""
        data = super().to_representation(instance)
        
        # 날짜 형식 변환
        if data['crawl_date']:
            data['crawl_date'] = data['crawl_date']
        if data['created_at']:
            data['created_at'] = data['created_at']
        
        # 키워드가 있으면 리스트로 변환
        if data['keyword']:
            data['keywords'] = [kw.strip() for kw in data['keyword'].split(',') if kw.strip()]
        else:
            data['keywords'] = []
        
        return data

class NewsListSerializer(serializers.ModelSerializer):
    """뉴스 목록용 간단한 시리얼라이저"""
    class Meta:
        model = News
        fields = ['id', 'title', 'keyword', 'link', 'crawl_date', 'created_at']
    
    def to_representation(self, instance):
        """목록에서도 링크 포함하여 표시"""
        data = super().to_representation(instance)
        
        # 키워드가 있으면 리스트로 변환
        if data['keyword']:
            data['keywords'] = [kw.strip() for kw in data['keyword'].split(',') if kw.strip()]
        else:
            data['keywords'] = []
        
        return data
