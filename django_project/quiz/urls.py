"""mysite URL Configuration

[...]
"""
from django.urls import path
from . import views
from .converter import *
urlpatterns = [
  #  path('login/<username>/', views.login_check),
  #  path('card/<username>/<int:pk>/<title>/<description>/', views.upload_card),
  #  path('getCard/<int:pk>/', views.get_card),
  #  path('quiz/<int:pk>/<question>/<answer>/', views.upload_quiz),
  #  path('delete/<int:pk>/', views.delete_card),
  #  path('likes/<int:pk>/<num:do_or_undo>/', views.like_card),
    path('', views.main, name='main'),
    path('search/', views.basic_search_view, name='basic_search'),
    path('search/detail', views.search_for_period, name='search'),
    path('search/time', views.search_for_selected_time, name='search_time'),
    path('download/', views.basic_download_view, name='basic_download'),
    path('download/detail', views.download_for_period, name='download'),
    path('download/time', views.download_for_selected_time, name='download_time'),
    path('make/', views.basic_make_view, name='basic_make'),
    path('make/detail', views.make_for_period, name='make'),
    path('visitors/', views.show_default_graph, name='visitors'),
    path('visitors/hourly/', views.show_num_of_visitors, name='hourly'),
    path('visitors/daily/', views.show_num_of_visitors, name='daily'),
    path('visitors/weekly/', views.show_num_of_visitors, name='weekly'),
    path('visitors/monthly/', views.show_num_of_visitors, name='monthly'),
    path('visitors/daily/detail/', views.show_visitors_detail, name='daily_detail'),
    path('visitors/weekly/detail/', views.show_visitors_detail, name='weekly_detail'),
    path('visitors/monthly/detail/', views.show_visitors_detail, name='monthly_detail'),
    path('cards/', views.show_card_list, name='cards'),
    path('cards/results/', views.show_card_list_searched, name='searched'),
    path('cards/results/retrieve/', views.retrive_card, name='retrieved'),
    path('/add_card_from_csv', views.add_card_from_csv, name='add_card_from_csv')
]