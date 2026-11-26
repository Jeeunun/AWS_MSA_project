from django.core.management.base import BaseCommand
from kbo.models import Team

class Command(BaseCommand):
    help = 'team_code가 비어있는 팀들을 수정합니다.'

    def handle(self, *args, **options):
        # team_code가 비어있는 팀들 찾기
        empty_code_teams = Team.objects.filter(team_code__isnull=True) | Team.objects.filter(team_code='')
        
        if not empty_code_teams.exists():
            self.stdout.write(
                self.style.SUCCESS('수정할 팀이 없습니다. 모든 팀의 team_code가 올바르게 설정되어 있습니다.')
            )
            return
        
        self.stdout.write(f'수정할 팀 수: {empty_code_teams.count()}')
        
        # 팀 이름을 기반으로 기본 team_code 설정
        team_code_mapping = {
            '두산': 'DS',
            '삼성': 'SS',
            '한화': 'HH',
            '키움': 'KI',
            'LG': 'LG',
            'KT': 'KT',
            'NC': 'NC',
            '롯데': 'LT',
            'SK': 'SK',
            'KIA': 'KT',
        }
        
        updated_count = 0
        for team in empty_code_teams:
            old_code = team.team_code or 'None'
            
            # 팀 이름을 기반으로 team_code 설정
            if team.team_name in team_code_mapping:
                team.team_code = team_code_mapping[team.team_name]
            else:
                # 팀 이름의 첫 글자들을 조합하여 기본 코드 생성
                team.team_code = team.team_name[:2].upper() if len(team.team_name) >= 2 else team.team_name.upper()
            
            team.save()
            updated_count += 1
            
            self.stdout.write(
                f'팀 "{team.team_name}"의 team_code를 "{old_code}"에서 "{team.team_code}"로 수정했습니다.'
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'총 {updated_count}개 팀의 team_code를 수정했습니다.')
        )
