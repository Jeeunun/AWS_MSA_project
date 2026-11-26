"""
KBO 앱에서 공통으로 사용되는 유틸리티 함수들
"""
from datetime import date
from typing import List, Dict, Optional, Any
from .models import Player, Team


# 상수 정의
CURRENT_YEAR = 2025
CURRENT_DATE = date(CURRENT_YEAR, 1, 1)

POSITION_MAPPING = {
    '투수': 'pitcher',
    '내야수': 'infielder', 
    '외야수': 'outfielder',
    '포수': 'catcher'
}


def calculate_player_age(birthdate: Optional[date], base_year: int = CURRENT_YEAR) -> Optional[int]:
    """
    선수의 나이를 계산합니다.
    
    Args:
        birthdate: 생년월일
        base_year: 기준 연도 (기본값: 2025)
    
    Returns:
        나이 (생일이 지나지 않았으면 1살 빼기)
    """
    if not birthdate:
        return None
    
    age = base_year - birthdate.year
    # 생일이 지나지 않았으면 1살 빼기
    if date(base_year, 1, 1) < birthdate.replace(year=base_year):
        age -= 1
    
    return age


def extract_numeric_value(value_str: Optional[str], unit: str) -> Optional[float]:
    """
    문자열에서 단위를 제거하고 숫자값을 추출합니다.
    
    Args:
        value_str: "180cm", "80kg" 등의 문자열
        unit: 제거할 단위 ("cm", "kg" 등)
    
    Returns:
        숫자값 또는 None
    """
    if not value_str:
        return None
    
    try:
        cleaned = str(value_str).replace(unit, '').strip()
        return float(cleaned)
    except ValueError:
        return None


def calculate_team_physical_stats(players: List[Player]) -> Dict[str, float]:
    """
    팀의 평균 키와 몸무게를 계산합니다.
    
    Args:
        players: 선수 목록
    
    Returns:
        평균 키와 몸무게가 포함된 딕셔너리
    """
    heights = [extract_numeric_value(p.height_cm, 'cm') for p in players if p.height_cm]
    weights = [extract_numeric_value(p.weight_kg, 'kg') for p in players if p.weight_kg]
    
    return {
        'avg_height': round(sum(heights) / len(heights), 1) if heights else 0,
        'avg_weight': round(sum(weights) / len(weights), 1) if weights else 0
    }


def classify_position(position_str: str) -> str:
    """
    한국어 포지션을 영어로 분류합니다.
    
    Args:
        position_str: 한국어 포지션 문자열
    
    Returns:
        영어 포지션 분류
    """
    if not position_str:
        return 'other'
    
    for korean, english in POSITION_MAPPING.items():
        if korean in position_str:
            return english
    
    return 'other'


def calculate_team_age_stats(players: List[Player], base_year: int = CURRENT_YEAR) -> Dict[str, Any]:
    """
    팀의 나이 통계를 계산합니다.
    
    Args:
        players: 선수 목록
        base_year: 기준 연도
    
    Returns:
        나이 통계가 포함된 딕셔너리
    """
    ages = []
    for player in players:
        age = calculate_player_age(player.birth, base_year)
        if age is not None:
            ages.append(age)
    
    if not ages:
        return {
            'avg_age': 0,
            'min_age': 0,
            'max_age': 0,
            'age_percentages': {'twenties': 0, 'thirties': 0, 'others': 0}
        }
    
    avg_age = round(sum(ages) / len(ages), 1)
    min_age = min(ages)
    max_age = max(ages)
    
    # 연령대별 분포 계산
    twenties = len([age for age in ages if 20 <= age <= 29])
    thirties = len([age for age in ages if 30 <= age <= 39])
    others = len([age for age in ages if age < 20 or age >= 40])
    
    age_percentages = {
        'twenties': round((twenties / len(ages)) * 100, 1),
        'thirties': round((thirties / len(ages)) * 100, 1),
        'others': round((others / len(ages)) * 100, 1)
    }
    
    return {
        'avg_age': avg_age,
        'min_age': min_age,
        'max_age': max_age,
        'age_percentages': age_percentages
    }


def get_position_counts(players: List[Player]) -> Dict[str, int]:
    """
    포지션별 선수 수를 계산합니다.
    
    Args:
        players: 선수 목록
    
    Returns:
        포지션별 선수 수가 포함된 딕셔너리
    """
    position_counts = {}
    
    for player in players:
        position = player.p_position.strip() if player.p_position else '기타'
        classified_pos = classify_position(position)
        position_counts[classified_pos] = position_counts.get(classified_pos, 0) + 1
    
    return position_counts


def calculate_position_percentages(position_counts: Dict[str, int], total_players: int) -> Dict[str, float]:
    """
    포지션별 퍼센트를 계산합니다.
    
    Args:
        position_counts: 포지션별 선수 수
        total_players: 전체 선수 수
    
    Returns:
        포지션별 퍼센트가 포함된 딕셔너리
    """
    if total_players == 0:
        return {}
    
    return {
        pos: round((count / total_players) * 100, 1)
        for pos, count in position_counts.items()
    }
