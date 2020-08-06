"""mysite URL Configuration

[...]
"""
from django.urls import path
from . import views
urlpatterns = [
    path('', views.main, name='main'),
    path('search/', views.basic_search_view, name='show'),
    path('search/graph', views.graph_for_category_view, name='search'),
    path('search/graph/detail', views.graph_detail_view, name='result'),
    path('visitors/', views.show_default_graph, name='visitors'),
    path('visitors/results/', views.show_num_of_visitors, name='results'),
    path('cards/', views.show_card_list, name='cards'),
    path('cards/results/', views.show_card_list_searched, name='searched'),
    path('cards/results/retrieve/', views.retrive_card, name='retrieved'),
]