import sys
from datetime import datetime, timezone as dt_tz
import boto3
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = (
        "Cognito(User Pool)와 로컬 DB 사용자 상태를 동기화합니다. "
        "Cognito에 없는 사용자는 로컬 DB에 deleted 표시, 존재하면 active로 표시합니다."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            help="특정 이메일만 동기화 (지정하지 않으면 모든 사용자)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="DB를 실제로 갱신하지 않고 변경될 내용만 출력",
        )
        parser.add_argument(
            "--profile",
            help="AWS 프로파일 이름(예: dugout-dev). settings.AWS_PROFILE보다 우선",
        )
        parser.add_argument(
            "--region",
            help="AWS 리전(예: ap-northeast-2). settings.AWS_REGION보다 우선",
        )

    # boto3 client 생성
    def _cognito_client(self, profile: str | None, region: str | None):
        profile = profile or getattr(settings, "AWS_PROFILE", None)
        region = region or getattr(settings, "AWS_REGION", "ap-northeast-2")
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        return session.client("cognito-idp", region_name=region)

    def handle(self, *args, **options):
        User = get_user_model()
        email_filter = options.get("email")
        dry_run = options.get("dry_run", False)
        profile = options.get("profile")
        region = options.get("region")

        user_pool_id = getattr(settings, "COGNITO_USER_POOL_ID", None)
        if not user_pool_id:
            raise CommandError("settings.COGNITO_USER_POOL_ID 가 필요합니다.")

        client = self._cognito_client(profile, region)

        # 동기화 대상 쿼리
        qs = User.objects.all()
        if email_filter:
            qs = qs.filter(email=email_filter)

        total = qs.count()
        found_active = 0
        marked_deleted = 0
        unknown = 0

        self.stdout.write(self.style.NOTICE(
            f"[sync] target users: {total}, dry_run={dry_run}, profile={profile or getattr(settings, 'AWS_PROFILE', None)}, region={region or getattr(settings, 'AWS_REGION', 'ap-northeast-2')}"
        ))

        # 처리 루프
        for u in qs.iterator():
            email = (u.email or "").strip()
            if not email:
                self.stdout.write(self.style.WARNING(f" - skip: id={u.id} username={u.username} (email 없음)"))
                unknown += 1
                continue

            try:
                client.admin_get_user(
                    UserPoolId=user_pool_id,
                    Username=email,
                )
                # Cognito에 존재 → active 로 마킹
                if getattr(u, "cognito_status", None) != "active" or u.cognito_deleted_at is not None:
                    self.stdout.write(f" - ACTIVE: {email}  (로컬 갱신: status→active, deleted_at→None)")
                    if not dry_run:
                        u.cognito_status = "active"
                        u.cognito_deleted_at = None
                        u.save(update_fields=["cognito_status", "cognito_deleted_at"])
                else:
                    self.stdout.write(f" - ACTIVE: {email}  (로컬 변경 없음)")
                found_active += 1

            except client.exceptions.UserNotFoundException:
                # Cognito에 없음 → deleted 마킹
                self._mark_deleted(u, dry_run)
                marked_deleted += 1

            except client.exceptions.ResourceNotFoundException:
                # 일부 상황에서 이 예외가 올 수 있음 → 없음과 동일 처리
                self._mark_deleted(u, dry_run)
                marked_deleted += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f" - ERROR: {email} → {e}"))
                unknown += 1

        self.stdout.write(self.style.SUCCESS(
            f"[done] active={found_active}, deleted={marked_deleted}, unknown={unknown}"
        ))

    def _mark_deleted(self, user, dry_run: bool):
        email = user.email
        if getattr(user, "cognito_status", None) != "deleted":
            self.stdout.write(f" - DELETED: {email}  (로컬 갱신: status→deleted, deleted_at→now)")
            if not dry_run:
                user.cognito_status = "deleted"
                user.cognito_deleted_at = datetime.now(dt_tz.utc)
                user.save(update_fields=["cognito_status", "cognito_deleted_at"])
        else:
            # 이미 deleted 인 경우 deleted_at 이 없다면 채워줌(선택)
            if user.cognito_deleted_at is None:
                self.stdout.write(f" - DELETED: {email}  (이미 deleted 상태 → deleted_at만 채움)")
                if not dry_run:
                    user.cognito_deleted_at = datetime.now(dt_tz.utc)
                    user.save(update_fields=["cognito_deleted_at"])
            else:
                self.stdout.write(f" - DELETED: {email}  (로컬 변경 없음)")
