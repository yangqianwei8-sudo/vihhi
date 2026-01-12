from django.contrib import admin
from backend.apps.accounts.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_username",
        "user_email",
        "mobile",
        "company",
        "department",
        "is_enabled",
        "updated_at",
    )
    search_fields = ("user__username", "user__email", "mobile")
    list_filter = ("company", "department", "is_enabled")
    ordering = ("user__username",)

    @admin.display(description="用户名")
    def user_username(self, obj):
        return obj.user.username

    @admin.display(description="邮箱")
    def user_email(self, obj):
        return obj.user.email
