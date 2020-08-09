"""mysite URL Configuration

[...]
"""
from django.urls import path
from . import views
urlpatterns = [
    path('', views.main, name='main'),
    path('search/', views.basic_search_view, name='show'),
    path('search/graph', views.search_for_period, name='search'),
   # path('search/graph/detail', views.graph_detail_view, name='result'),
    path('download/', views.basic_download_view, name='basic_download'),
    path('download/detail', views.download_for_period, name='download'),
    path('make/', views.basic_make_view, name='basic_make'),
    path('make/detail', views.make_for_period, name='make'),
    path('visitors/', views.show_default_graph, name='visitors'),
    path('visitors/results/', views.show_num_of_visitors, name='results'),
    path('cards/', views.show_card_list, name='cards'),
    path('cards/results/', views.show_card_list_searched, name='searched'),
    path('cards/results/retrieve/', views.retrive_card, name='retrieved'),
]