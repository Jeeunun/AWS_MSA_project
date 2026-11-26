from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Avg, Min, Max, Case, When, IntegerField
from django.db.models.functions import ExtractYear, Length
from datetime import date, datetime
from typing import Any, Dict, List
from .models import Team, Player
from .utils import (
    calculate_player_age, calculate_team_physical_stats, 
    calculate_team_age_stats, get_position_counts, 
    calculate_position_percentages, CURRENT_YEAR, CURRENT_DATE
)
import csv
import re
# AWS S3 관련 import
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os
import json

def get_s3_player_image_url(team_code: str, player_name: str, player_number: str | None = None) -> str | None:
    """
    S3에서 선수 이미지 URL을 검색해 반환합니다.
    실제 업로드 구조: players/ 디렉터리 바로 아래에 파일이 위치하며, 파일명은
    "{팀코드}_{등번호}_{이름}_...jpg" 형태입니다. 예) players/DS_00_김재호_내야수.jpg
    """
    print(f"🔍 S3 이미지 검색 시작: team={team_code}, name={player_name}, number={player_number} (타입: {type(player_number)})")
    
    try:
        # S3 환경변수 확인
        bucket_name = os.environ.get('AWS_S3_BUCKET', '')
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID', '')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
        aws_region = os.environ.get('AWS_DEFAULT_REGION', '')
        
        print(f"🔑 환경변수 확인:")
        print(f"  - BUCKET: {bucket_name}")
        print(f"  - ACCESS_KEY: {aws_access_key[:10]}...")
        print(f"  - SECRET_KEY: {aws_secret_key[:10]}...")
        print(f"  - REGION: {aws_region}")
        
        if not bucket_name:
            print('⚠️  AWS_S3_BUCKET 환경변수가 설정되지 않았습니다.')
            return None
        
        if not aws_access_key or not aws_secret_key:
            print('⚠️  AWS 인증 정보가 설정되지 않았습니다.')
            return None
        
        # S3 클라이언트 초기화
        print("🚀 S3 클라이언트 초기화 중...")
        s3_client = boto3.client('s3')
        print("✅ S3 클라이언트 초기화 완료")

        base_prefix = f"players/{team_code}_"
        print(f"🔍 검색 프리픽스: {base_prefix}")

        def name_candidates(name: str):
            candidates = [name, name.replace(' ', ''), name.replace(' ', '_')]
            print(f"🔍 이름 후보: {candidates}")
            return candidates

        # 1) 등번호가 있으면 번호 프리픽스를 우선 시도 (0패딩/무패딩 모두)
        if player_number and str(player_number).isdigit():
            print(f"🔍 등번호 기반 검색 시작: {player_number}")
            raw = str(int(player_number))  # 무패딩
            padded2 = raw.zfill(2)
            padded3 = raw.zfill(3)
            print(f"🔍 검색할 번호들: {raw}, {padded2}, {padded3}")
            
            for num in [raw, padded2, padded3]:
                try:
                    prefix = f"{base_prefix}{num}_"
                    print(f"🔍 S3 검색 시도: {prefix}")
                    resp = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=100)
                    print(f"🔍 S3 응답: {len(resp.get('Contents', []))}개 객체 발견")
                    
                    for obj in resp.get('Contents', []):
                        key = obj['Key']
                        print(f"🔍 검사 중인 객체: {key}")
                        if any(cand in key for cand in name_candidates(player_name)):
                            url = f"https://{bucket_name}.s3.ap-northeast-2.amazonaws.com/{key}"
                            print(f"✅ 이미지 발견: {url}")
                            return url
                except Exception as e:
                    # 다음 케이스 시도
                    print(f"⚠️  번호 {num} 프리픽스 검색 실패: {e}")

        # 2) 팀코드만으로 브로드 검색 후 이름 포함 파일 찾기
        try:
            resp = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=base_prefix, MaxKeys=1000)
            for obj in resp.get('Contents', []):
                key = obj['Key']
                if any(cand in key for cand in name_candidates(player_name)):
                    return f"https://{bucket_name}.s3.ap-northeast-2.amazonaws.com/{key}"
        except Exception as e:
            print(f"⚠️  팀코드 기반 브로드 검색 실패: {e}")

        print(f"⚠️  S3에서 이미지 미발견: team={team_code}, name={player_name}, number={player_number}")
        return None
    except NoCredentialsError:
        print("❌ AWS 인증 정보가 없습니다")
        return None
    except ClientError as e:
        print(f"❌ S3 클라이언트 오류: {e}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None

def team_list(request):
    # 디버깅을 위한 로깅 추가
    print("=== team_list 뷰 디버깅 ===")
    
    teams = (
        Team.objects.select_related('manager')
        .filter(team_code__isnull=False)  # team_code가 None이 아닌 팀만
        .exclude(team_code='')  # team_code가 빈 문자열이 아닌 팀만
        .annotate(player_count=Count('players'))
        .order_by('team_name')
    )
    
    print(f"팀 수: {teams.count()}")
    
    # 각 팀의 상세 정보 확인
    for team in teams:
        print(f"팀: {team.team_name}")
        print(f"  - 팀코드: {team.team_code}")
        print(f"  - 선수수: {team.player_count}")
        try:
            manager = team.manager
            print(f"  - 감독: {manager.m_name}")
        except Exception as e:
            print(f"  - 감독 오류: {e}")
        print()
    
    # 추가 컨텍스트 변수들
    total_players = sum(team.player_count for team in teams)
    total_managers = teams.count()  # 각 팀마다 감독이 있으므로
    
    context = {
        'teams': teams,
        'total_players': total_players,
        'total_managers': total_managers,
    }
    
    return render(request, 'kbo/team_list.html', context)


def team_detail(request, code: str):
    team = get_object_or_404(Team, team_code=code)
    
    # 디버깅을 위한 로깅 추가
    print(f"=== team_detail 뷰 디버깅 ===")
    print(f"팀: {team.team_name} ({team.team_code})")
    print(f"팀 ID: {team.team_id}")
    
    # Filters
    pos = request.GET.get('pos', '').strip()
    sort = request.GET.get('sort', 'num').strip()  # num | name | pos
    page = int(request.GET.get('page', '1') or 1)
    per_page = int(request.GET.get('per', '50') or 50)

    qs = team.players.all()
    print(f"전체 선수 수: {qs.count()}")
    
    if pos:
        qs = qs.filter(p_position__icontains=pos)
        print(f"포지션 '{pos}' 필터링 후: {qs.count()}명")

    filtered_count = qs.count()
    
    # 선수 데이터 샘플 확인
    print("=== 선수 데이터 샘플 ===")
    sample_players = qs[:5]
    for player in sample_players:
        print(f"  - {player.p_number}번 {player.p_name} ({player.p_position})")
        print(f"    키: {player.height_cm}, 몸무게: {player.weight_kg}, 생년월일: {player.birth}")

    # numeric-friendly ordering for p_number
    qs = qs.annotate(
        bn_len=Length('p_number'),
        bn_empty=Case(
            When(p_number__isnull=True, then=1),
            When(p_number=0, then=1),
            default=0,
            output_field=IntegerField(),
        ),
    )

    if sort == 'name':
        qs = qs.order_by('p_name')
    elif sort == 'pos':
        qs = qs.order_by('p_position', 'bn_empty', 'bn_len', 'p_number')
    else:  # 'num'
        qs = qs.order_by('bn_empty', 'bn_len', 'p_number', 'p_name')

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page)

    # JSON export for AJAX requests
    if request.GET.get('format') == 'json':
        players_data = []
        for p in qs:
                    players_data.append({
            'id': p.idx,
            'name': p.p_name,
            'p_number': p.p_number,
            'position': p.p_position,
            'height': p.height_cm,
            'weight': p.weight_kg,
            'birthdate': p.birth.isoformat() if p.birth else None,
            'bats_throws': p.p_info,
        })
        return JsonResponse({
            'team_name': team.team_name,
            'team_code': team.team_code,
            'players': players_data,
            'total_count': len(players_data)
        })
    
    # CSV export (kept for internal use; links may be hidden)
    if request.GET.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{team.team_code}_players.csv"'
        writer = csv.writer(response)
        writer.writerow(['팀', '등번호', '이름', '포지션', '키', '몸무게', '생년월일', '투타정보'])
        for p in qs:
            writer.writerow([
                team.team_name,
                p.p_number,
                p.p_name,
                p.p_position,
                p.height_cm,
                p.weight_kg,
                p.birth.isoformat() if p.birth else '',
                p.p_info,
            ])
        return response

    positions = (
        team.players.exclude(p_position='').values_list('p_position', flat=True).distinct().order_by('p_position')
    )
    
    # 포지션별 선수 수 계산 (리스트 형태로)
    position_stats = []
    for pos_name in positions:
        position_stats.append({
            'name': pos_name,
            'count': team.players.filter(p_position=pos_name).count()
        })

    # 팀별 선수 수 계산 (사이드바용)
    all_teams = Team.objects.all()
    team_player_counts = {}
    for t in all_teams:
        team_player_counts[t.team_code] = t.players.count()
    
    # 포지션별 선수 수 계산
    pitchers_count = team.players.filter(p_position__icontains='투수').count()
    position_players_count = filtered_count - pitchers_count
    
    return render(
        request,
        'kbo/team_detail.html',
        {
            'team': team,
            'players': page_obj,
            'positions': positions,
            'position_stats': position_stats,
            'pos': pos,
            'sort': sort,
            'per_page': per_page,
            'total_players': filtered_count,
            'teams': all_teams,  # 다른 팀 목록
            'team_player_counts': team_player_counts,  # 팀별 선수 수
            'pitchers_count': pitchers_count,
            'position_players_count': position_players_count,
        }
    )


def stats_analysis(request):
    """데이터 분석 페이지"""
    try:
        # 디버깅을 위한 로깅 추가
        print("=== stats_analysis 뷰 디버깅 ===")
        
        # 전체 선수 수
        total_players = Player.objects.count()
        print(f"전체 선수 수: {total_players}")
        
        # 팀별 선수 수 및 나이 계산
        team_stats = []
        from django.db.models import Count
        teams = Team.objects.annotate(player_count=Count('players')).all()
        print(f"전체 팀 수: {teams.count()}")
        
        for team in teams:
            players = team.players.all()
            player_count = players.count()
            print(f"팀 '{team.team_name}'의 선수 수: {player_count}")
            
            # 포지션별 선수 수 계산
            pitchers = players.filter(p_position__icontains='투수').count()
            catchers = players.filter(p_position__icontains='포수').count()
            infielders = players.filter(p_position__icontains='내야수').count()
            outfielders = players.filter(p_position__icontains='외야수').count()
            
            # 투타별 선수 수 계산
            right_batters = players.filter(p_info__icontains='우타').count()
            left_batters = players.filter(p_info__icontains='좌타').count()
            right_pitchers = players.filter(p_info__icontains='우투').count()
            left_pitchers = players.filter(p_info__icontains='좌투').count()
            
            # 유틸리티 함수를 사용하여 나이 통계 계산
            age_stats = calculate_team_age_stats(players)
            
            team_stats.append({
                'name': team.team_name,
                'code': team.team_code,
                'player_count': player_count,
                'pitchers': pitchers,
                'catchers': catchers,
                'infielders': infielders,
                'outfielders': outfielders,
                'right_batters': right_batters,
                'left_batters': left_batters,
                'right_pitchers': right_pitchers,
                'left_pitchers': left_pitchers,
                'avg_age': age_stats['avg_age'],
                'min_age': age_stats['min_age'],
                'max_age': age_stats['max_age']
            })
        
        # 선수 수 기준으로 정렬
        team_stats.sort(key=lambda x: x['player_count'], reverse=True)
        
        # 포지션별 선수 분포
        position_stats = Player.objects.exclude(p_position='').values('p_position').annotate(
            count=Count('idx')
        ).order_by('-count')
        print(f"포지션별 통계: {list(position_stats)}")
        
        # 연령대별 분포
        age_groups = {
            '20대 이하': Player.objects.filter(birth__year__gte=CURRENT_YEAR-20).count(),
            '21-25세': Player.objects.filter(birth__year__range=(CURRENT_YEAR-25, CURRENT_YEAR-21)).count(),
            '26-30세': Player.objects.filter(birth__year__range=(CURRENT_YEAR-30, CURRENT_YEAR-26)).count(),
            '31-35세': Player.objects.filter(birth__year__range=(CURRENT_YEAR-35, CURRENT_YEAR-31)).count(),
            '36세 이상': Player.objects.filter(birth__year__lt=CURRENT_YEAR-35).count(),
        }
        print(f"연령대별 분포: {age_groups}")
        
        # 팀별 포지션 분포
        team_position_stats = {}
        for team in teams:
            positions = team.players.exclude(p_position='').values('p_position').annotate(
                count=Count('idx')
            ).order_by('-count')
            team_position_stats[team.team_code] = {
                'name': team.team_name,
                'positions': list(positions)
            }
        
        # 추가 컨텍스트 변수들
        total_teams = teams.count()
        total_managers = total_teams  # 각 팀마다 감독이 있으므로
        avg_players_per_team = round(total_players / total_teams, 1) if total_teams > 0 else 0
        
        print(f"최종 통계 - 팀: {total_teams}, 선수: {total_players}, 감독: {total_managers}")
        
        return render(request, 'kbo/stats_analysis.html', {
            'total_players': total_players,
            'total_teams': total_teams,
            'total_managers': total_managers,
            'avg_players_per_team': avg_players_per_team,
            'teams': teams,  # 팀 버튼용 teams 변수 추가
            'team_stats': team_stats,
            'position_stats': position_stats,
            'age_groups': age_groups,
            'team_position_stats': team_position_stats,
        })
        
    except Exception as e:
        # 오류 발생 시 로깅
        print(f"통계 분석 페이지 오류: {e}")
        import traceback
        traceback.print_exc()
        
        # 기본 컨텍스트로 렌더링
        return render(request, 'kbo/stats_analysis.html', {
            'total_players': 0,
            'total_teams': 0,
            'total_managers': 0,
            'avg_players_per_team': 0,
            'teams': [],
            'team_stats': [],
            'position_stats': [],
            'age_groups': {},
            'team_position_stats': {},
            'error_message': f'데이터를 불러오는 중 오류가 발생했습니다: {str(e)}'
        })

def search_advanced(request):
    """고급 검색 페이지"""
    name = request.GET.get('name', '').strip()
    team_code = request.GET.get('team', '').strip()
    position = request.GET.get('position', '').strip()
    bats = request.GET.get('bats', '').strip()
    throws = request.GET.get('throws', '').strip()
    min_height = request.GET.get('min_height', '').strip()
    max_height = request.GET.get('max_height', '').strip()
    min_weight = request.GET.get('min_weight', '').strip()
    page = int(request.GET.get('page', '1') or 1)
    per_page = int(request.GET.get('per', '50') or 50)

    qs = Player.objects.select_related('team')
    
    # 기본 검색
    if name:
        qs = qs.filter(p_name__icontains=name)
    if team_code:
        qs = qs.filter(team__team_code=team_code)
    if position:
        # 포지션 코드를 실제 포지션명으로 변환
        position_map = {
            'P': '투수',
            'C': '포수', 
            'IF': '내야수',
            'OF': '외야수'
        }
        if position in position_map:
            qs = qs.filter(p_position__icontains=position_map[position])
    if bats:
        qs = qs.filter(p_info__icontains=bats)
    if throws:
        qs = qs.filter(p_info__icontains=throws)
    
    # 키/몸무게 검색
    if min_height:
        try:
            qs = qs.filter(height_cm__gte=int(min_height))
        except ValueError:
            pass
    if max_height:
        try:
            qs = qs.filter(height_cm__lte=int(max_height))
        except ValueError:
            pass
    if min_weight:
        try:
            qs = qs.filter(weight_kg__gte=int(min_weight))
        except ValueError:
            pass

    # 기본 정렬 (이름순)
    qs = qs.order_by('p_name', 'team__team_name')

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page)

    teams = Team.objects.order_by('team_name').values('team_name', 'team_code')
    positions = Player.objects.exclude(p_position='').values_list('p_position', flat=True).distinct().order_by('p_position')

    return render(request, 'kbo/search_advanced.html', {
        'teams': teams,
        'total_results': qs.count(),
        'page_obj': page_obj,
        'name': name,
        'team_code': team_code,
        'position': position,
        'bats': bats,
        'throws': throws,
        'min_height': min_height,
        'max_height': max_height,
        'min_weight': min_weight,
        'per_page': per_page,
        'positions': positions,
    })

def team_position_stats_api(request):
    """팀별 포지션 통계를 JSON으로 제공하는 API"""
    try:
        teams_data = []
        
        for team in Team.objects.all():
            # 팀의 선수들 가져오기
            players = team.players.all()
            total_players = players.count()
            
            if total_players == 0:
                continue
            
            # 유틸리티 함수를 사용하여 포지션별 선수 수 계산
            position_counts = get_position_counts(players)
            
            # 유틸리티 함수를 사용하여 퍼센트 계산
            position_percentages = calculate_position_percentages(position_counts, total_players)
            
            # 유틸리티 함수를 사용하여 연령별 분포 계산
            age_stats = calculate_team_age_stats(players)
            age_percentages = age_stats['age_percentages']
            
            teams_data.append({
                'code': team.team_code,
                'name': team.team_name,
                'total_players': total_players,
                'position_percentages': position_percentages,
                'age_percentages': age_percentages
            })
        
        return JsonResponse({
            'success': True,
            'teams': teams_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def team_comparison(request):
    """팀 구성 비교 페이지"""
    team_code1 = request.GET.get('team1', '').strip()
    team_code2 = request.GET.get('team2', '').strip()
    
    teams = Team.objects.order_by('team_name')
    
    if team_code1 and team_code2:
        team1 = get_object_or_404(Team, team_code=team_code1)
        team2 = get_object_or_404(Team, team_code=team_code2)
        
        # 팀별 기본 통계
        # 유틸리티 함수를 사용하여 나이 통계 계산
        team1_age_stats = calculate_team_age_stats(team1.players.all())
        team2_age_stats = calculate_team_age_stats(team2.players.all())
        
        team1_avg_age = team1_age_stats['avg_age']
        team2_avg_age = team2_age_stats['avg_age']
        
        # 팀1 포지션별 선수 수 계산
        team1_position_counts = get_position_counts(team1.players.all())
        team1.pitcher_count = team1_position_counts.get('pitcher', 0)
        team1.infielder_count = team1_position_counts.get('infielder', 0)
        team1.outfielder_count = team1_position_counts.get('outfielder', 0)
        team1.catcher_count = team1_position_counts.get('catcher', 0)
        team1.player_count = team1.players.count()  # 총 선수 수 추가
        
        # 팀2 포지션별 선수 수 계산
        team2_position_counts = get_position_counts(team2.players.all())
        team2.pitcher_count = team2_position_counts.get('pitcher', 0)
        team2.infielder_count = team2_position_counts.get('infielder', 0)
        team2.outfielder_count = team2_position_counts.get('outfielder', 0)
        team2.catcher_count = team2_position_counts.get('catcher', 0)
        team2.player_count = team2.players.count()  # 총 선수 수 추가
        
        # 팀1 키/몸무게 평균 계산
        team1_physical_stats = calculate_team_physical_stats(team1.players.all())
        team1_avg_height = team1_physical_stats['avg_height']
        team1_avg_weight = team1_physical_stats['avg_weight']
        
        # 팀2 키/몸무게 평균 계산
        team2_physical_stats = calculate_team_physical_stats(team2.players.all())
        team2_avg_height = team2_physical_stats['avg_height']
        team2_avg_weight = team2_physical_stats['avg_weight']
        
        # 차이 계산
        total_players_diff = team1.players.count() - team2.players.count()
        pitchers_diff = team1_position_counts.get('pitcher', 0) - team2_position_counts.get('pitcher', 0)
        position_players_diff = (team1_position_counts.get('infielder', 0) + team1_position_counts.get('outfielder', 0) + team1_position_counts.get('catcher', 0)) - (team2_position_counts.get('infielder', 0) + team2_position_counts.get('outfielder', 0) + team2_position_counts.get('catcher', 0))
        
        team1_stats = {
            'total_players': team1.players.count(),
            'pitchers': team1_position_counts.get('pitcher', 0),
            'position_players': team1_position_counts.get('infielder', 0) + team1_position_counts.get('outfielder', 0) + team1_position_counts.get('catcher', 0),
            'catchers': team1_position_counts.get('catcher', 0),
            'infielders': team1_position_counts.get('infielder', 0),
            'outfielders': team1_position_counts.get('outfielder', 0),
            'right_batters': team1.players.filter(p_info__contains='우타').count(),
            'left_batters': team1.players.filter(p_info__contains='좌타').count(),
            'right_pitchers': team1.players.filter(p_info__contains='우투').count(),
            'left_pitchers': team1.players.filter(p_info__contains='좌투').count(),
            'avg_age': team1_avg_age,
            'avg_height': team1_avg_height,
            'avg_weight': team1_avg_weight,
        }
        
        team2_stats = {
            'total_players': team2.players.count(),
            'pitchers': team2_position_counts.get('pitcher', 0),
            'position_players': team2_position_counts.get('infielder', 0) + team2_position_counts.get('outfielder', 0) + team2_position_counts.get('catcher', 0),
            'catchers': team2_position_counts.get('catcher', 0),
            'infielders': team2_position_counts.get('infielder', 0),
            'outfielders': team2_position_counts.get('outfielder', 0),
            'right_batters': team2.players.filter(p_info__contains='우타').count(),
            'left_batters': team2.players.filter(p_info__contains='좌타').count(),
            'right_pitchers': team2.players.filter(p_info__contains='우투').count(),
            'left_pitchers': team2.players.filter(p_info__contains='좌투').count(),
            'avg_age': team2_avg_age,
            'avg_height': team2_avg_height,
            'avg_weight': team2_avg_weight,
        }
        
        # 차이 통계 추가
        comparison_stats = {
            'total_players_diff': total_players_diff,
            'pitchers_diff': pitchers_diff,
            'position_players_diff': position_players_diff,
        }
        
        return render(request, 'kbo/team_comparison.html', {
            'teams': teams,
            'team1': team1,
            'team2': team2,
            'team1_stats': team1_stats,
            'team2_stats': team2_stats,
            'comparison_stats': comparison_stats,
            'team_code1': team_code1,
            'team_code2': team_code2,
        })
    
    return render(request, 'kbo/team_comparison.html', {
        'teams': teams,
    })

def player_detail_modal(request, player_id):
    """선수 상세 정보 모달용 뷰"""
    try:
        player = Player.objects.select_related('team').get(idx=player_id)
        
        # 선수 번호 추출 (p_number 필드에서)
        player_number = player.p_number if hasattr(player, 'p_number') and player.p_number else None
        
        # S3에서 이미지 URL 가져오기 (선수 번호 포함하여 정확한 이미지 찾기)
        s3_image_url = get_s3_player_image_url(player.team.team_code, player.p_name, player_number)
        if s3_image_url:
            player.image_url = s3_image_url
            # 데이터베이스에도 업데이트
            player.save()
        
        # 이전/다음 선수 정보 가져오기 (팀 전체 기준)
        team_players = player.team.players.all().order_by('p_number', 'p_name')
        player_list = list(team_players)
        
        current_index = -1
        for i, p in enumerate(player_list):
            if p.idx == player.idx:
                current_index = i
                break
        
        prev_player = None
        next_player = None
        
        if current_index > 0:
            prev_player = player_list[current_index - 1]
        if current_index < len(player_list) - 1:
            next_player = player_list[current_index + 1]
        
        return render(request, 'kbo/player_detail_modal.html', {
            'player': player,
            'prev_player': prev_player,
            'next_player': next_player,
        })
    except Player.DoesNotExist:
        return JsonResponse({'error': '선수를 찾을 수 없습니다.'}, status=404)

def get_all_players_json(request):
    """모든 선수의 상세 정보를 JSON으로 반환하는 API"""
    players = Player.objects.select_related('team').all()
    data = []
    for p in players:
        data.append({
            'id': p.idx,
            'name': p.p_name,
            'team_name': p.team.team_name,
            'p_number': p.p_number,
            'position': p.p_position,
        })
    return JsonResponse({'players': data}, safe=False)