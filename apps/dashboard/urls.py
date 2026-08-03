from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('dashboard/', views.index, name='index'),
    path('dashboard/infra/', views.infra_view, name='infra'),
    path('dashboard/vpn/', views.vpn_view, name='vpn'),
    path('dashboard/cofre/', views.cofre_view, name='cofre'),
    path('dashboard/ferramentas/', views.ferramentas_view, name='ferramentas'),
    path('dashboard/governanca/', views.governanca_view, name='governanca'),
    path('dashboard/simular/<str:acao>/', views.simular_acao, name='simular_acao'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
