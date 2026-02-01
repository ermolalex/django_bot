from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Profile, Company

class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "inn", "channel_id", "channel_name", "verified")

admin.site.register(Company, CompanyAdmin)


class ProfileAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Fields', {'fields': ('phone', 'tg_id', 'company')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Profile Fields', {'fields': ('phone', 'tg_id', 'company')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'phone', 'tg_id', 'company')


admin.site.register(Profile, ProfileAdmin)
