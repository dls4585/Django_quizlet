"""mysite URL Configuration

[...]
"""
from django.urls import path
from . import views
urlpatterns = [
    path('', views.basic_search_view, name='show'),
    path('search', views.graph_for_category_view, name='search'),
    path('search/period', views.graph_detail_view, name='result')
]