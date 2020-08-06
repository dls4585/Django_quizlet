"""mysite URL Configuration

[...]
"""
from django.urls import path
from . import views
urlpatterns = [
    path('', views.show, name='show'),
    path('search', views.period_search, name='search'),
    path('search/period', views.show_result, name='result')
]