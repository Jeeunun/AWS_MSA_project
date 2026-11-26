# events/management/commands/settle_predictions.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Result, Predict, Coupon
from django.db.models import Q

class Command(BaseCommand):
    help = "경기 종료분 정답 정산 및 쿠폰 지급"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        # 종료 & winner 세팅된 경기만
        finished = Result.objects.filter(status="종료", winner__isnull=False, date__lte=now)
        issued = 0
        for r in finished:
            winners = Predict.objects.filter(
                result=r,
                predicted=("AWAY" if r.winner == r.away_team else "HOME")
            )
            for p in winners:
                if not hasattr(p, "coupon"):
                    Coupon.objects.create(
                        token_id=p.token_id,
                        code=self.make_code(),
                        status=0,
                        expire_at=now + timezone.timedelta(days=7),
                        predict=p,
                    )
                    issued += 1
        self.stdout.write(self.style.SUCCESS(f"정산 완료: 쿠폰 {issued}건 발급"))

    @staticmethod
    def make_code(n=12):
        import secrets, string
        abc = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(abc) for _ in range(n))
