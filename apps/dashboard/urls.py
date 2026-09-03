from django.urls import path
from . import views
from . import api_views

app_name = 'dashboard'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('dashboard/', views.index, name='index'),
    path('dashboard/infra/', views.infra_view, name='infra'),
    path('dashboard/workspace/', views.workspace_view, name='workspace'),
    path('dashboard/integracoes/', views.integracoes_view, name='integracoes'),
    path('dashboard/integracoes/ongsys/', views.ongsys_integration_view, name='ongsys_integration'),
    path('dashboard/integracoes/ongsys/sync/', views.ongsys_trigger_sync_async_view, name='ongsys_trigger_sync'),
    path('dashboard/integracoes/ongsys/api/<str:endpoint_key>/', views.ongsys_api_proxy_view, name='ongsys_api_proxy'),
    path('dashboard/integracoes/ongsys/report/pdf/', views.ongsys_download_report_pdf_view, name='ongsys_report_pdf'),
    path('dashboard/integracoes/ongsys/report/data/', views.ongsys_report_data_view, name='ongsys_report_data'),
    path('dashboard/integracoes/ongsys/async/test-all/', views.ongsys_trigger_test_all_async_view, name='ongsys_async_test_all'),
    path('dashboard/integracoes/ongsys/async/sync-db/', views.ongsys_trigger_sync_async_view, name='ongsys_async_sync_db'),
    path('dashboard/integracoes/ongsys/async/task-status/<str:task_id>/', views.ongsys_task_status_view, name='ongsys_task_status'),


    path('dashboard/integracoes/transportes/', views.transportes_integration_view, name='transportes_integracao'),
    path('dashboard/integracoes/transportes/arquivos-data/', views.transportes_arquivos_mensais_data_view, name='transportes_arquivos_data'),
    path('dashboard/integracoes/transportes/corridas-data/', views.transportes_corridas_data_view, name='transportes_corridas_data'),
    path('dashboard/integracoes/transportes/upload/', views.transportes_upload_lote_view, name='transportes_upload_lote'),
    path('dashboard/integracoes/transportes/api/<str:provider>/<str:endpoint_key>/', views.transportes_api_proxy_view, name='transportes_api_proxy'),

    # 🚗 API REST Pública / M2M de Transportes (Uber & 99)
    path('api/v1/transportes/corridas/', views.transportes_api_corridas_view, name='api_transportes_corridas'),
    path('api/v1/transportes/metricas/', views.transportes_api_metricas_view, name='api_transportes_metricas'),
    path('api/v1/transportes/arquivos/', views.transportes_api_arquivos_view, name='api_transportes_arquivos'),
    path('api/v1/transportes/fechamentos/', views.transportes_api_fechamentos_view, name='api_transportes_fechamentos'),
    path('api/v1/transportes/programas/', views.transportes_api_programas_view, name='api_transportes_programas'),
    path('api/v1/transportes/colaboradores/', views.transportes_api_colaboradores_view, name='api_transportes_colaboradores'),
    path('api/v1/transportes/exportar/', views.transportes_exportar_excel_view, name='api_transportes_exportar'),

    path('dashboard/integracoes/ecosistema/', views.ecosistema_m2m_view, name='ecosistema_m2m'),

    path('dashboard/vpn/', views.vpn_view, name='vpn'),
    path('dashboard/cofre/', views.cofre_view, name='cofre'),
    path('dashboard/ferramentas/', views.ferramentas_view, name='ferramentas'),
    path('dashboard/formularios/', views.formularios_view, name='formularios'),
    path('dashboard/formularios/cadastro-sistema/', views.formulario_cadastro_sistema_pagina, name='formulario_cadastro_sistema_pagina'),
    path('dashboard/formularios/avaliacao-servicos/', views.formulario_avaliacao_servicos_pagina, name='formulario_avaliacao_servicos_pagina'),
    path('dashboard/formularios/suporte-ti/', views.formulario_suporte_ti_pagina, name='formulario_suporte_ti_pagina'),
    path('dashboard/formularios/novo-sistema/', views.submeter_cadastro_sistema, name='submeter_cadastro_sistema'),
    path('dashboard/formularios/submeter/', views.submeter_resposta_formulario, name='submeter_resposta_formulario'),
    path('dashboard/governanca/', views.governanca_view, name='governanca'),
    path('dashboard/simular/<str:acao>/', views.simular_acao, name='simular_acao'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # 🔌 Rotas da API M2M (Hub de Microsserviços)
    path('api/internal/auth/verify/', api_views.auth_verify_view, name='api_auth_verify'),
    path('api/internal/workspace/data/', api_views.workspace_data_view, name='api_workspace_data'),
    path('api/internal/webhooks/notify/', api_views.webhooks_notify_view, name='api_webhooks_notify'),
]
