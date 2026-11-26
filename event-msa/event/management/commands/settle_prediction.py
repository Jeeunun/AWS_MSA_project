# events/management/commands/settle_predictions.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from ...models import Schedule, Predict, Coupon
from django.db.models import Q

class Command(BaseCommand):
    help = "경기 종료분 정답 정산 및 쿠폰 지급"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        # 종료 & winner 세팅된 경기만
        finished = Schedule.objects.filter(gameStatus="END", winner__isnull=False, match_date__lte=timezone.localdate(),)
        issued = 0
        for r in finished:
            # winner 값을 대문자로 변환하여 비교 (predicted는 대문자로 저장됨)
            winner_upper = r.winner.upper() if r.winner else None
            self.stdout.write(f"경기 {r.idx}: winner='{r.winner}' -> '{winner_upper}'")
            
            winners = Predict.objects.filter(
                schedule=r,
                predicted__iexact=winner_upper,     #대소문자무시
            )
            self.stdout.write(f"  예측 일치하는 사용자: {winners.count()}명")
            
            for p in winners:
                obj, created = Coupon.objects.get_or_create(
                    predict=p,
                    defaults={
                        "code": self.make_code(),
                        "coupon_status": 2,  
                        "expire_at": timezone.now() + timezone.timedelta(days=7),
                    },
                )
                if created:
                    issued += 1
                    
        self.stdout.write(self.style.SUCCESS(f"정산 완료: 쿠폰 {issued}건 발급"))

    @staticmethod
    def make_code(n=12):
        import secrets, string
        abc = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(abc) for _ in range(n))
