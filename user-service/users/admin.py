from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 기본 필드셋 + 우리 확장 필드
    fieldsets = UserAdmin.fieldsets + (
        ("Extra", {"fields": ("name", "tel", "birth", "gender", "team", "token_id",
                              "cognito_status", "cognito_deleted_at")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Extra", {"fields": ("name", "tel", "birth", "gender", "team", "token_id")}),
    )

    # 리스트 컬럼 커스터마이즈
    list_display = (
        "username", "email", "name", "team",
        "cognito_status_badge", "cognito_deleted_at",
        "is_staff", "last_login",
    )
    list_filter = ("cognito_status", "is_staff", "is_superuser", "team")
    search_fields = ("username", "email", "name", "team")
    readonly_fields = ("cognito_deleted_at",)  # 삭제시각은 읽기전용

    def cognito_status_badge(self, obj):
        status = (obj.cognito_status or "").lower()
        if status == "deleted":
            return format_html('<span style="padding:2px 8px;border-radius:10px;background:#fee2e2;color:#991b1b;">🔴 deleted</span>')
        elif status == "disabled":
            return format_html('<span style="padding:2px 8px;border-radius:10px;background:#fde68a;color:#92400e;">🟡 disabled</span>')
        elif status == "active":
            return format_html('<span style="padding:2px 8px;border-radius:10px;background:#dcfce7;color:#166534;">🟢 active</span>')
        else:
            return format_html('<span style="padding:2px 8px;border-radius:10px;background:#e5e7eb;color:#374151;">⚪ unknown</span>')
    cognito_status_badge.short_description = "Cognito 상태"


