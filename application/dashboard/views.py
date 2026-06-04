"""
Views for Power BI Dashboard Integration
"""

from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
import json


class DashboardView(View):
    """Display Power BI Dashboard"""
    
    template_name = 'dashboard/powerbi_dashboard.html'
    
    # Power BI Embed Configuration
    POWERBI_REPORT_ID = 'a3b6aa0f-43e0-45a7-882f-82fdc64055b4'
    POWERBI_TENANT_ID = '5047bca2-da88-442e-a09a-d9b8af692adc'
    POWERBI_WORKSPACE_ID = ''  # Optional: add workspace ID if needed
    
    def get(self, request):
        """Render dashboard with Power BI embed"""
        context = {
            'report_id': self.POWERBI_REPORT_ID,
            'tenant_id': self.POWERBI_TENANT_ID,
            'embed_url': self.get_embed_url(),
            'direct_url': self.get_direct_url(),
        }
        return render(request, self.template_name, context)
    
    def get_embed_url(self):
        """Generate Power BI embed URL - iframe embedding"""
        # Standard Power BI embed URL - simpler without extra config
        return (
            f"https://app.powerbi.com/reportEmbed?"
            f"reportId={self.POWERBI_REPORT_ID}&"
            f"autoAuth=true"
        )
    
    def get_direct_url(self):
        """Generate direct Power BI URL for opening in new window"""
        # Use direct link to Power BI service for better reliability
        return (
            f"https://app.powerbi.com/groups/me/reports/{self.POWERBI_REPORT_ID}"
        )
    
    def get_service_url(self):
        """Generate Power BI Service URL for sign in"""
        return "https://app.powerbi.com"
