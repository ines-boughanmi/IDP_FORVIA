"""
URL Configuration for Dashboard App
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='powerbi'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
]
