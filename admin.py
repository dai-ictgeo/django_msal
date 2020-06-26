from django.contrib import admin

from .models import MicrosoftTenant, MicrosoftUser

@admin.register(MicrosoftTenant)
class MicrosoftTenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'tid', 'is_active')

@admin.register(MicrosoftUser)
class MicrosoftUserAdmin(admin.ModelAdmin):
    list_display = ('name', 'preferred_username', 'oid', 'tenant')
