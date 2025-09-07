from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('nearest_stop/', views.nearest_stop, name='nearest_stop'),
]
