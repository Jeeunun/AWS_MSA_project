from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from datetime import datetime

from .models import Team, Player, Manager
from .serializers import (
    TeamListSerializer, TeamDetailSerializer, 
    PlayerSerializer, ManagerSerializer
)

@api_view(['GET'])
@permission_classes([AllowAny])
def teams_list_api(request):
    """
    팀 목록 API
    GET /api/info/teams/
    """
    try:
        teams = Team.objects.all().order_by('team_name')
        serializer = TeamListSerializer(teams, many=True)
        
        # 통계 정보 계산
        total_players = Player.objects.count()
        total_managers = Manager.objects.count()
        last_update = datetime.now().strftime('%Y-%m-%d')
        
        return Response({
            'teams': serializer.data,
            'total_players': total_players,
            'total_managers': total_managers,
            'last_update': last_update
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'팀 목록 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def team_detail_api(request, team_code):
    """
    팀 상세 정보 API
    GET /api/info/teams/{team_code}/
    """
    try:
        print(f"=== team_detail_api 디버깅 ===")
        print(f"요청된 team_code: {team_code}")
        
        team = get_object_or_404(Team, team_code=team_code)
        print(f"찾은 팀: {team}")
        print(f"팀 ID: {team.team_id}")
        print(f"팀명: {team.team_name}")
        print(f"팀 코드: {team.team_code}")
        
        # 관련 데이터 확인
        players_count = team.players.count()
        print(f"연결된 선수 수: {players_count}")
        
        try:
            manager = team.manager
            print(f"감독: {manager.m_name if manager else '없음'}")
        except:
            print(f"감독: 없음")
        
        serializer = TeamDetailSerializer(team)
        serialized_data = serializer.data
        print(f"시리얼라이저 결과: {serialized_data}")
        
        response_data = {
            'team': serialized_data
        }
        print(f"최종 응답 데이터: {response_data}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'팀 상세 정보 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def players_search_api(request):
    """
    선수 검색 API
    GET /api/info/players/search/
    """
    try:
        print(f"=== players_search_api 디버깅 ===")
        
        # 검색 파라미터
        name = request.GET.get('name', '')
        team = request.GET.get('team', '')
        position = request.GET.get('position', '')
        bats = request.GET.get('bats', '')
        throws = request.GET.get('throws', '')
        min_height = request.GET.get('min_height', '')
        max_height = request.GET.get('max_height', '')
        min_weight = request.GET.get('min_weight', '')
        
        print(f"검색 파라미터:")
        print(f"  - name: '{name}'")
        print(f"  - team: '{team}'")
        print(f"  - position: '{position}'")
        print(f"  - bats: '{bats}'")
        print(f"  - throws: '{throws}'")
        print(f"  - min_height: '{min_height}'")
        print(f"  - max_height: '{max_height}'")
        print(f"  - min_weight: '{min_weight}'")
        
        # 기본 쿼리셋
        queryset = Player.objects.select_related('team').all()
        print(f"초기 쿼리셋 선수 수: {queryset.count()}")
        
        # 필터 적용
        if name:
            queryset = queryset.filter(p_name__icontains=name)
            print(f"이름 필터 적용 후: {queryset.count()}명")
        
        if team:
            print(f"팀 필터 적용 전: {queryset.count()}명")
            print(f"팀 코드 '{team}'으로 필터링...")
            queryset = queryset.filter(team__team_code=team)
            print(f"팀 필터 적용 후: {queryset.count()}명")
            
            # 팀별 선수 수 확인
            team_players = Player.objects.filter(team__team_code=team)
            print(f"팀 '{team}'의 전체 선수 수: {team_players.count()}명")
            print(f"팀 '{team}'의 선수들:")
            for p in team_players[:5]:  # 처음 5명만 출력
                print(f"  - {p.p_name} ({p.p_position})")
        
        if position:
            print(f"포지션 필터 적용 전: {queryset.count()}명")
            print(f"포지션 '{position}'으로 필터링...")
            
            # 포지션 매핑 (영문 코드 → 한글 이름)
            position_mapping = {
                'P': '투수',
                'C': '포수', 
                'IF': '내야수',
                'OF': '외야수'
            }
            
            # 매핑된 포지션으로 필터링
            mapped_position = position_mapping.get(position, position)
            print(f"매핑된 포지션: '{position}' → '{mapped_position}'")
            
            queryset = queryset.filter(p_position=mapped_position)
            print(f"포지션 필터 적용 후: {queryset.count()}명")
            
            # 포지션별 선수 수 확인
            if team:
                pos_players = Player.objects.filter(team__team_code=team, p_position=mapped_position)
                print(f"팀 '{team}'의 포지션 '{mapped_position}' 선수 수: {pos_players.count()}명")
        
        if bats:
            queryset = queryset.filter(p_info__icontains=bats)
            print(f"타격 필터 적용 후: {queryset.count()}명")
        
        if throws:
            queryset = queryset.filter(p_info__icontains=throws)
            print(f"투구 필터 적용 후: {queryset.count()}명")
        
        if min_height:
            try:
                min_h = int(min_height)
                queryset = queryset.filter(height_cm__gte=min_h)
                print(f"최소 키 필터 적용 후: {queryset.count()}명")
            except ValueError:
                print(f"최소 키 파싱 실패: {min_height}")
                pass
        
        if max_height:
            try:
                max_h = int(max_height)
                queryset = queryset.filter(height_cm__lte=max_h)
                print(f"최대 키 필터 적용 후: {queryset.count()}명")
            except ValueError:
                print(f"최대 키 파싱 실패: {max_height}")
                pass
        
        if min_weight:
            try:
                min_w = int(min_weight)
                queryset = queryset.filter(weight_kg__gte=min_w)
                print(f"최소 몸무게 필터 적용 후: {queryset.count()}명")
            except ValueError:
                print(f"최소 몸무게 파싱 실패: {min_weight}")
                pass
        
        # 정렬
        queryset = queryset.order_by('team__team_name', 'p_number')
        
        serializer = PlayerSerializer(queryset, many=True)
        final_count = queryset.count()
        print(f"최종 검색 결과: {final_count}명")
        
        return Response({
            'players': serializer.data,
            'total_count': final_count,
            'filters': {
                'name': name,
                'team': team,
                'position': position,
                'bats': bats,
                'throws': throws,
                'min_height': min_height,
                'max_height': max_height,
                'min_weight': min_weight
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"players_search_api 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'선수 검색 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def player_detail_api(request, player_id):
    """
    선수 상세 정보 API
    GET /api/info/players/{player_id}/
    """
    try:
        player = get_object_or_404(Player, idx=player_id)
        serializer = PlayerSerializer(player)
        
        return Response({
            'player': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'선수 상세 정보 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def teams_options_api(request):
    """
    팀 옵션 API (검색용)
    GET /api/info/teams/options/
    """
    try:
        print(f"=== teams_options_api 디버깅 ===")
        print(f"Team 모델 확인: {Team}")
        print(f"Team 모델 필드: {[f.name for f in Team._meta.fields]}")
        
        # 전체 팀 수 확인
        total_teams = Team.objects.count()
        print(f"전체 팀 수: {total_teams}")
        
        if total_teams == 0:
            print("경고: 데이터베이스에 팀이 없습니다!")
            return Response({
                'teams': [],
                'message': '데이터베이스에 팀이 없습니다.'
            }, status=status.HTTP_200_OK)
        
        # 팀 데이터 조회
        teams = Team.objects.values('team_code', 'team_name').order_by('team_name')
        teams_list = list(teams)
        print(f"조회된 팀 목록: {teams_list}")
        
        return Response({
            'teams': teams_list
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"teams_options_api 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'팀 옵션 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def positions_options_api(request):
    """
    포지션 옵션 API
    GET /api/info/positions/options/
    """
    try:
        positions = [
            {'value': 'P', 'label': '투수'},
            {'value': 'C', 'label': '포수'},
            {'value': 'IF', 'label': '내야수'},
            {'value': 'OF', 'label': '외야수'}
        ]
        
        return Response({
            'positions': positions
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'포지션 옵션 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def stats_analysis_api(request):
    """
    통계분석 API
    GET /api/info/stats/analysis/
    """
    try:
        print(f"=== stats_analysis_api 디버깅 ===")
        
        # 전체 통계 계산
        total_teams = Team.objects.count()
        total_players = Player.objects.count()
        total_managers = Manager.objects.count()
        avg_players_per_team = round(total_players / total_teams, 1) if total_teams > 0 else 0
        
        print(f"전체 통계:")
        print(f"  - 팀 수: {total_teams}")
        print(f"  - 선수 수: {total_players}")
        print(f"  - 감독 수: {total_managers}")
        print(f"  - 팀당 평균 선수: {avg_players_per_team}")
        
        # 포지션별 통계
        pitchers = Player.objects.filter(p_position='투수').count()
        catchers = Player.objects.filter(p_position='포수').count()
        infielders = Player.objects.filter(p_position='내야수').count()
        outfielders = Player.objects.filter(p_position='외야수').count()
        
        print(f"포지션별 통계:")
        print(f"  - 투수: {pitchers}명")
        print(f"  - 포수: {catchers}명")
        print(f"  - 내야수: {infielders}명")
        print(f"  - 외야수: {outfielders}명")
        
        # 팀별 상세 통계
        team_stats = []
        teams = Team.objects.all()
        
        for team in teams:
            team_players = Player.objects.filter(team=team)
            total_team_players = team_players.count()
            
            if total_team_players > 0:
                # 포지션별 선수 수
                team_pitchers = team_players.filter(p_position='투수').count()
                team_catchers = team_players.filter(p_position='포수').count()
                team_infielders = team_players.filter(p_position='내야수').count()
                team_outfielders = team_players.filter(p_position='외야수').count()
                
                                 # 투타 정보 분석
                right_batters = team_players.filter(p_info__icontains='우타').count()
                left_batters = team_players.filter(p_info__icontains='좌타').count()
                right_pitchers = team_players.filter(p_position='투수', p_info__icontains='우투').count()
                left_pitchers = team_players.filter(p_position='투수', p_info__icontains='좌투').count()
                 
                team_stat = {
                    'teamName': team.team_name,  # React에서 기대하는 필드명으로 변경
                    'totalPlayers': total_team_players,
                    'pitchers': team_pitchers,
                    'catchers': team_catchers,
                    'infielders': team_infielders,
                    'outfielders': team_outfielders,
                    'rightBatters': right_batters,
                    'leftBatters': left_batters,
                    'rightPitchers': right_pitchers,
                    'leftPitchers': left_pitchers
                }
                
                team_stats.append(team_stat)
                print(f"팀 '{team.team_name}' 통계: {team_stat}")
        
        # 응답 데이터 구성
        response_data = {
            'summary': {
                'totalTeams': total_teams,
                'totalPlayers': total_players,
                'totalManagers': total_managers,
                'avgPlayersPerTeam': avg_players_per_team
            },
            'positionStats': {
                'pitchers': pitchers,
                'catchers': catchers,
                'infielders': infielders,
                'outfielders': outfielders
            },
            'teamStats': team_stats
        }
        
        print(f"최종 응답 데이터 구성 완료")
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"stats_analysis_api 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'통계분석 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def team_comparison_api(request):
    """
    팀 비교 API
    GET /api/info/teams/compare/?team1=KIA&team2=LG
    """
    try:
        print(f"=== team_comparison_api 디버깅 ===")
        
        # 요청 파라미터
        team1_code = request.GET.get('team1', '')
        team2_code = request.GET.get('team2', '')
        
        print(f"비교 요청: {team1_code} vs {team2_code}")
        
        if not team1_code or not team2_code:
            return Response({
                'error': '두 팀의 코드를 모두 제공해야 합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if team1_code == team2_code:
            return Response({
                'error': '서로 다른 팀을 선택해야 합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 팀 정보 조회
        try:
            team1 = Team.objects.get(team_code=team1_code)
            team2 = Team.objects.get(team_code=team2_code)
        except Team.DoesNotExist as e:
            return Response({
                'error': f'팀을 찾을 수 없습니다: {str(e)}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        print(f"팀1: {team1.team_name} ({team1.team_code})")
        print(f"팀2: {team2.team_name} ({team2.team_code})")
        
        # 팀별 선수 통계 계산
        def get_team_stats(team):
            team_players = Player.objects.filter(team=team)
            total_players = team_players.count()
            
            if total_players == 0:
                return {
                    'total_players': 0,
                    'pitchers': 0,
                    'position_players': 0,
                    'catchers': 0,
                    'infielders': 0,
                    'outfielders': 0,
                    'right_batters': 0,
                    'left_batters': 0,
                    'right_pitchers': 0,
                    'left_pitchers': 0
                }
            
            # 포지션별 선수 수
            pitchers = team_players.filter(p_position='투수').count()
            catchers = team_players.filter(p_position='포수').count()
            infielders = team_players.filter(p_position='내야수').count()
            outfielders = team_players.filter(p_position='외야수').count()
            position_players = catchers + infielders + outfielders
            
            # 투타 정보 분석
            right_batters = team_players.filter(p_info__icontains='우타').count()
            left_batters = team_players.filter(p_info__icontains='좌타').count()
            right_pitchers = team_players.filter(p_position='투수', p_info__icontains='우투').count()
            left_pitchers = team_players.filter(p_position='투수', p_info__icontains='좌투').count()
            
            return {
                'total_players': total_players,
                'pitchers': pitchers,
                'position_players': position_players,
                'catchers': catchers,
                'infielders': infielders,
                'outfielders': outfielders,
                'right_batters': right_batters,
                'left_batters': left_batters,
                'right_pitchers': right_pitchers,
                'left_pitchers': left_pitchers
            }
        
        # 두 팀의 통계 계산
        team1_stats = get_team_stats(team1)
        team2_stats = get_team_stats(team2)
        
        print(f"팀1 통계: {team1_stats}")
        print(f"팀2 통계: {team2_stats}")
        
        # 응답 데이터 구성
        response_data = {
            'team1': {
                'code': team1.team_code,
                'name': team1.team_name,
                'stats': team1_stats
            },
            'team2': {
                'code': team2.team_code,
                'name': team2.team_name,
                'stats': team2_stats
            }
        }
        
        print(f"팀 비교 데이터 구성 완료")
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"team_comparison_api 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'팀 비교 조회 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
