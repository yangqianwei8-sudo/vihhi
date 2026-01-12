from django.contrib import admin
from backend.apps.org.models import Company, Department


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "is_active", "created_at")
    search_fields = ("name", "code")
    list_filter = ("is_active",)
    ordering = ("code",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "company", "parent", "is_active", "created_at")
    search_fields = ("name", "company__name", "company__code")
    list_filter = ("company", "is_active")
    ordering = ("company__code", "name")
