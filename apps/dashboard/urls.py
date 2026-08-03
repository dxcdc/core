from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('dashboard/', views.index, name='index'),
    path('dashboard/simular/<str:acao>/', views.simular_acao, name='simular_acao'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
