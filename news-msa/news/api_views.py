from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from datetime import date, datetime

from .models import News
from .serializers import NewsSerializer, NewsListSerializer

class NewsPagination(PageNumberPagination):
    """News Service용 페이지네이션"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

def get_user_from_request(request):
    """요청에서 사용자 정보 추출"""
    if hasattr(request, 'user') and request.user.is_authenticated:
        return request.user.username, request.user.username
    return None, None

@api_view(['GET'])
@permission_classes([AllowAny])
def news_list_api(request):
    """
    뉴스 목록 API
    GET /api/news/
    """
    try:
        # 쿼리 파라미터 처리
        category = request.GET.get('category', '')  # 카테고리 필터
        keyword = request.GET.get('keyword', '')    # 키워드 검색
        date_filter = request.GET.get('date', '')   # 날짜 필터
        
        # 기본 쿼리셋
        queryset = News.objects.all().order_by('-created_at')
        
        # 카테고리 필터링 (키워드 기반)
        if category:
            queryset = queryset.filter(keyword__icontains=category)
        
        # 키워드 검색 (제목 + 키워드)
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) | 
                Q(keyword__icontains=keyword)
            )
        
        # 날짜 필터링
        if date_filter:
            try:
                filter_date = date.fromisoformat(date_filter)
                queryset = queryset.filter(crawl_date=filter_date)
            except ValueError:
                pass  # 잘못된 날짜 형식은 무시
        
        # 페이지네이션 적용
        paginator = NewsPagination()
        paginated_news = paginator.paginate_queryset(queryset, request)
        
        # 시리얼라이징
        serializer = NewsListSerializer(paginated_news, many=True)
        
        return paginator.get_paginated_response({
            'news': serializer.data,
            'filters': {
                'category': category,
                'keyword': keyword,
                'date': date_filter,
                'today': timezone.localdate().isoformat()
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'뉴스 목록 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def news_detail_api(request, news_id):
    """
    뉴스 상세 API
    GET /api/news/{news_id}/
    """
    try:
        news = get_object_or_404(News, id=news_id)
        serializer = NewsSerializer(news)
        
        return Response({
            'news': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'뉴스 상세 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def news_search_api(request):
    """
    뉴스 검색 API
    GET /api/news/search/
    """
    try:
        query = request.GET.get('q', '')
        if not query:
            return Response({
                'error': '검색어를 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 제목과 키워드에서 검색
        queryset = News.objects.filter(
            Q(title__icontains=query) | 
            Q(keyword__icontains=query)
        ).order_by('-created_at')
        
        # 페이지네이션 적용
        paginator = NewsPagination()
        paginated_news = paginator.paginate_queryset(queryset, request)
        
        # 시리얼라이징
        serializer = NewsListSerializer(paginated_news, many=True)
        
        return paginator.get_paginated_response({
            'news': serializer.data,
            'search_query': query,
            'total_results': queryset.count()
        })
        
    except Exception as e:
        return Response({
            'error': f'뉴스 검색 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def news_categories_api(request):
    """
    뉴스 카테고리 목록 API
    GET /api/news/categories/
    """
    try:
        # 키워드 기반으로 카테고리 추출
        categories = set()
        news_list = News.objects.values_list('keyword', flat=True).distinct()
        
        for keywords in news_list:
            if keywords:
                for keyword in keywords.split(','):
                    clean_keyword = keyword.strip()
                    if clean_keyword:
                        categories.add(clean_keyword)
        
        return Response({
            'categories': sorted(list(categories)),
            'total_count': len(categories)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'카테고리 목록 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def news_today_api(request):
    """
    오늘의 뉴스 API
    GET /api/news/today/
    """
    try:
        today = timezone.localdate()
        today_news = News.objects.filter(crawl_date=today).order_by('-created_at')
        
        # 페이지네이션 적용
        paginator = NewsPagination()
        paginated_news = paginator.paginate_queryset(today_news, request)
        
        # 시리얼라이징
        serializer = NewsListSerializer(paginated_news, many=True)
        
        return paginator.get_paginated_response({
            'news': serializer.data,
            'date': today.isoformat(),
            'total_count': today_news.count()
        })
        
    except Exception as e:
        return Response({
            'error': f'오늘의 뉴스 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


