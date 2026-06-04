"""
Django Admin Configuration for Dashboard App
"""

from django.contrib import admin
from .models import DashboardConfiguration


@admin.register(DashboardConfiguration)
class DashboardConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'report_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Configuration', {
            'fields': ('name', 'is_active')
        }),
        ('Power BI Settings', {
            'fields': ('report_id', 'tenant_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
