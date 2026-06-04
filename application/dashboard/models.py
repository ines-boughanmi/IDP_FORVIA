"""
Models for Dashboard App
"""

from django.db import models


class DashboardConfiguration(models.Model):
    """Store Power BI Dashboard Configuration"""
    
    name = models.CharField(max_length=255, default="IDP Monitoring Dashboard")
    report_id = models.CharField(max_length=255, default="a3b6aa0f-43e0-45a7-882f-82fdc64055b4")
    tenant_id = models.CharField(max_length=255, default="5047bca2-da88-442e-a09a-d9b8af692adc")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Dashboard Configuration"
        verbose_name_plural = "Dashboard Configurations"
