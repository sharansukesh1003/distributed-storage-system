from django.urls import path
from . import views

urlpatterns = [
    path('metrics/', views.container_dashboard, name='container_dashboard'),
]
