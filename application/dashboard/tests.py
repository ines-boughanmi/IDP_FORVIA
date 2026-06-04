"""
Tests for Dashboard App
"""

from django.test import TestCase, Client
from django.urls import reverse
from .models import DashboardConfiguration


class DashboardViewTests(TestCase):
    """Test cases for dashboard views"""
    
    def setUp(self):
        self.client = Client()
        self.dashboard_config = DashboardConfiguration.objects.create(
            name="Test Dashboard",
            report_id="a3b6aa0f-43e0-45a7-882f-82fdc64055b4",
            tenant_id="5047bca2-da88-442e-a09a-d9b8af692adc"
        )
    
    def test_dashboard_view_get_200(self):
        """Test that dashboard view returns 200 status code"""
        response = self.client.get(reverse('dashboard:powerbi'))
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_view_uses_correct_template(self):
        """Test that dashboard view uses the correct template"""
        response = self.client.get(reverse('dashboard:powerbi'))
        self.assertTemplateUsed(response, 'dashboard/powerbi_dashboard.html')
    
    def test_dashboard_view_context(self):
        """Test that dashboard view passes correct context"""
        response = self.client.get(reverse('dashboard:powerbi'))
        self.assertIn('report_id', response.context)
        self.assertIn('tenant_id', response.context)
        self.assertIn('embed_url', response.context)
    
    def test_embed_url_generation(self):
        """Test that embed URL is correctly generated"""
        response = self.client.get(reverse('dashboard:powerbi'))
        embed_url = response.context['embed_url']
        
        self.assertIn('reportEmbed', embed_url)
        self.assertIn('a3b6aa0f-43e0-45a7-882f-82fdc64055b4', embed_url)
        self.assertIn('autoAuth=true', embed_url)


class DashboardModelTests(TestCase):
    """Test cases for dashboard models"""
    
    def test_create_dashboard_configuration(self):
        """Test creating a dashboard configuration"""
        config = DashboardConfiguration.objects.create(
            name="Production Dashboard",
            report_id="test-report-id",
            tenant_id="test-tenant-id"
        )
        self.assertEqual(config.name, "Production Dashboard")
        self.assertTrue(config.is_active)
    
    def test_dashboard_configuration_str(self):
        """Test dashboard configuration string representation"""
        config = DashboardConfiguration.objects.create(
            name="Test Config"
        )
        self.assertEqual(str(config), "Test Config")
