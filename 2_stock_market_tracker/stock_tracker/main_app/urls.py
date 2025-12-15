from django.urls import path
from . import views

urlpatterns = [
    path('', views.stock_chart_view, name='home'),
]