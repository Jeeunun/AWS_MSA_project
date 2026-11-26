from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count
from django.db import IntegrityError, transaction
from datetime import date, datetime, time as time_cls

from .models import Schedule, Predict, Coupon, TotalRank, AttackRank, DefenseRank, Season
from .serializers import (
    ScheduleSerializer, PredictSerializer, PredictCreateSerializer,
    CouponSerializer, TotalRankSerializer, AttackRankSerializer, DefenseRankSerializer
)

class EventPagination(PageNumberPagination):
    """Event Service용 페이지네이션"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

def get_user_from_request(request):
    """요청에서 사용자 정보 추출"""
    if hasattr(request, 'user') and request.user.is_authenticated:
        # JWT에서 cognito:username을 user_id로 사용 (로그인 시 입력한 ID)
        return request.user.username, request.user.username
    return None, None

@api_view(['GET'])
@permission_classes([AllowAny])
def schedule_list_api(request):
    """
    경기 일정/결과 목록 API
    GET /api/event/schedules/
    """
    try:
        # 날짜 필터링
        q_date = request.GET.get('date')
        
        # 기본 쿼리
        queryset = Schedule.objects.all().order_by('-match_date', 'startTime')
        
        # 날짜 필터링 적용
        if q_date:
            try:
                filter_date = date.fromisoformat(q_date)
                queryset = queryset.filter(match_date=filter_date)
            except ValueError:
                pass  # 잘못된 날짜 형식은 무시
        
        # 페이지네이션 적용
        paginator = EventPagination()
        paginated_schedules = paginator.paginate_queryset(queryset, request)
        
        # 시리얼라이징
        serializer = ScheduleSerializer(paginated_schedules, many=True)
        
        return paginator.get_paginated_response({
            'schedules': serializer.data,
            'selected_date': q_date,
            'today': timezone.localdate().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': f'경기 일정 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def participate_api(request):
    """
    이벤트 참여 페이지 API
    GET /api/event/participate/
    """
    try:
        user_id, username = get_user_from_request(request)
        
        # 현재 시점 기준 가장 가까운 '경기전' 경기
        now = timezone.localdate()
        base = Schedule.objects.filter(gameStatus="BEFORE", match_date__gte=now).order_by("match_date")
        
        match = None
        if base.exists():
            nearest = base.first().match_date
            match = base.filter(match_date=nearest).order_by("?").first()
        
        # 참여 현황 집계
        aggregation = {"away": 0, "home": 0, "total": 0}
        if match:
            for result in (Predict.objects.filter(schedule=match)
                          .values("predicted").annotate(count=Count("idx"))):
                if result["predicted"] == "AWAY":
                    aggregation["away"] = result["count"]
                elif result["predicted"] == "HOME":
                    aggregation["home"] = result["count"]
            aggregation["total"] = aggregation["away"] + aggregation["home"]
        
        # 내 참여 내역 (인증된 사용자만)
        history = []
        if user_id:
            history_queryset = (Predict.objects
                              .filter(user_id=user_id)
                              .select_related("schedule")
                              .order_by("-schedule__match_date")[:20])
            history = PredictSerializer(history_queryset, many=True).data
        
        response_data = {
            'match': ScheduleSerializer(match).data if match else None,
            'aggregation': aggregation,
            'history': history,
            'now': timezone.localdate().isoformat()
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'참여 정보 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote_api(request):
    """
    투표 API
    POST /api/event/vote/
    """
    try:
        user_id, username = get_user_from_request(request)
        if not user_id:
            return Response({
                'ok': False,
                'msg': '로그인이 필요합니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 입력 검증
        result_id = request.data.get("result_id")
        choice = request.data.get("choice")
        
        if not result_id or not str(result_id).isdigit():
            return Response({
                'ok': False,
                'msg': '잘못된 요청(result_id 누락)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if choice not in ("AWAY", "HOME"):
            return Response({
                'ok': False,
                'msg': '잘못된 선택'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 경기 로드
        try:
            match = Schedule.objects.get(pk=int(result_id))
        except Schedule.DoesNotExist:
            return Response({
                'ok': False,
                'msg': '경기를 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 시작 시간 기준 차단
        try:
            h, m = map(int, (match.startTime or "00:00").strip().split(":"))
        except Exception:
            h, m = 0, 0
        
        start_naive = datetime.combine(match.match_date, time_cls(hour=h, minute=m))
        start_dt = timezone.make_aware(start_naive, timezone.get_current_timezone())
        
        if timezone.now() >= start_dt or match.gameStatus != "BEFORE":
            return Response({
                'ok': False,
                'msg': '경기가 시작되어 참여할 수 없습니다.'
            }, status=status.HTTP_409_CONFLICT)
        
        # 하루 1회 제한
        if Predict.objects.filter(user_id=user_id, schedule__match_date=match.match_date).exists():
            return Response({
                'ok': False,
                'msg': '오늘은 이미 참여하셨어요.'
            }, status=status.HTTP_409_CONFLICT)
        
        # 저장
        try:
            with transaction.atomic():
                Predict.objects.create(
                    user_id=user_id,
                    predicted=choice,
                    schedule=match
                )
        except IntegrityError:
            return Response({
                'ok': False,
                'msg': '오늘은 이미 참여하셨어요.'
            }, status=status.HTTP_409_CONFLICT)
        
        return Response({
            'ok': True,
            'msg': '이벤트 참여 완료!'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'ok': False,
            'msg': f'서버 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def coupons_api(request):
    """
    쿠폰 현황 API
    GET /api/event/coupons/
    """
    try:
        user_id, username = get_user_from_request(request)
        if not user_id:
            return Response({
                'error': '인증이 필요합니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 사용자 쿠폰 조회
        coupons_queryset = (Coupon.objects
                           .select_related("predict")
                           .filter(predict__user_id=user_id)
                           .order_by("-created_at"))
        
        serializer = CouponSerializer(coupons_queryset, many=True)
        
        response_data = {
            'display_name': username or '사용자',
            'user_id': user_id,
            'coupons': serializer.data,
            'total_count': coupons_queryset.count(),
            'now': timezone.now().isoformat()
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'쿠폰 정보 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def ranks_api(request):
    """
    순위 정보 API
    GET /api/event/ranks/
    """
    try:
        # 현재 시즌 조회
        current_season = Season.objects.filter(
            startDate__lte=timezone.localdate(),
            endDate__gte=timezone.localdate()
        ).first()
        
        if not current_season:
            # 현재 시즌이 없으면 최신 시즌 조회
            current_season = Season.objects.order_by('-season').first()
        
        if current_season:
            # 현재/최신 시즌의 순위 데이터만 조회
            total_ranks = TotalRank.objects.filter(season=current_season).order_by('rank')
            attack_ranks = AttackRank.objects.filter(season=current_season).order_by('rank')
            defense_ranks = DefenseRank.objects.filter(season=current_season).order_by('rank')
        else:
            # 시즌 데이터가 없으면 빈 결과
            total_ranks = TotalRank.objects.none()
            attack_ranks = AttackRank.objects.none()
            defense_ranks = DefenseRank.objects.none()
        
        response_data = {
            'total': TotalRankSerializer(total_ranks, many=True).data,
            'attack': AttackRankSerializer(attack_ranks, many=True).data,
            'defense': DefenseRankSerializer(defense_ranks, many=True).data,
            'season': current_season.season if current_season else None
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'순위 정보 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def user_history_api(request):
    """
    사용자 이벤트 참여내역 조회 API
    GET /api/event/user-history/?user_id=123
    """
    try:
        user_id = request.GET.get('user_id')
        if not user_id:
            return Response({
                'error': 'user_id 파라미터가 필요합니다.'
            }, status=400)
        
        print(f"[EVENT USER HISTORY] 사용자 참여내역 조회 - user_id: {user_id}")
        
        # 사용자의 모든 예측 내역 조회 (최신순)
        user_predictions = Predict.objects.filter(user_id=user_id).select_related('schedule').order_by('-created_at')
        
        events = []
        total_predictions = 0
        correct_predictions = 0
        
        for predict in user_predictions:
            schedule = predict.schedule
            
            # 결과 판정 (경기가 끝났고 결과가 있는 경우)
            is_correct = None
            if schedule.gameStatus == "END" and schedule.winner is not None:
                # Schedule.winner 값을 대문자로 변환하여 비교 (predicted는 대문자로 저장됨)
                actual_winner = schedule.winner.upper()
                is_correct = predict.predicted == actual_winner
                if is_correct:
                    correct_predictions += 1
            
            event_data = {
                'predict_id': predict.idx,
                'predicted': predict.predicted,
                'created_at': predict.created_at,
                'schedule': {
                    'match_date': schedule.match_date,
                    'home_team': schedule.homeTeamName,
                    'away_team': schedule.awayTeamName,
                    'game_status': schedule.gameStatus,
                    'home_score': schedule.homeResult,
                    'away_score': schedule.awayResult
                },
                'is_correct': is_correct
            }
            events.append(event_data)
            total_predictions += 1
        
        # 통계 계산
        accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
        
        statistics = {
            'total_predictions': total_predictions,
            'correct_predictions': correct_predictions,
            'accuracy': round(accuracy, 1)
        }
        
        print(f"[EVENT USER HISTORY] 조회 완료 - 총 {total_predictions}개, 정답률 {accuracy:.1f}%")
        
        return Response({
            'message': '사용자 참여내역 조회 성공',
            'events': events,
            'statistics': statistics
        }, status=200)
    
    except Exception as e:
        print(f"[EVENT USER HISTORY] 오류: {e}")
        return Response({
            'error': '참여내역 조회 중 오류가 발생했습니다.'
        }, status=500)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_user_data_api(request):
    """
    사용자 데이터 삭제 API (탈퇴용)
    DELETE /api/event/delete-user-data/
    """
    try:
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({
                'error': 'user_id 파라미터가 필요합니다.'
            }, status=400)
        
        print(f"[EVENT DELETE USER DATA] 사용자 데이터 삭제 시작 - user_id: {user_id}")
        
        # 해당 사용자의 예측 데이터 조회
        user_predictions = Predict.objects.filter(user_id=user_id)
        prediction_count = user_predictions.count()
        
        # 해당 예측들과 연결된 쿠폰들 조회
        coupon_count = 0
        for prediction in user_predictions:
            try:
                coupon = prediction.coupon
                coupon.delete()
                coupon_count += 1
            except Coupon.DoesNotExist:
                pass  # 쿠폰이 없는 예측은 무시
        
        # 예측 데이터 삭제
        deleted_predictions = user_predictions.delete()
        
        print(f"[EVENT DELETE USER DATA] 삭제 완료 - 예측: {prediction_count}개, 쿠폰: {coupon_count}개")
        
        return Response({
            'message': '사용자 데이터 삭제 완료',
            'deleted_predictions': prediction_count,
            'deleted_coupons': coupon_count
        }, status=200)
    
    except Exception as e:
        print(f"[EVENT DELETE USER DATA] 오류: {e}")
        return Response({
            'error': '사용자 데이터 삭제 중 오류가 발생했습니다.'
        }, status=500)