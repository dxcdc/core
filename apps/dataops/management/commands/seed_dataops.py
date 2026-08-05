from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from apps.dataops.models import UsuarioDataOps, GrupoWorkspace, MembroGrupo, NotaFiscalConciliacao, LogAuditoria, EstruturaVpn

class Command(BaseCommand):
    help = 'Popula o banco de dados local do CDC Core com o cenário hipotético DataOps'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Inicializando carga de dados hipotéticos do CDC DataOps...'))

        # 0. Garante a existência do superusuário dxcdc
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u_dxcdc, created = User.objects.get_or_create(username='dxcdc', defaults={'email': 'dxcdc@cdc.org.br', 'is_staff': True, 'is_superuser': True})
        u_dxcdc.set_password('admindx!')
        u_dxcdc.is_staff = True
        u_dxcdc.is_superuser = True
        u_dxcdc.save()

        # 1. Usuários do Workspace
        u_admin, _ = UsuarioDataOps.objects.get_or_create(
            email='fvier@cdc.org.br',
            defaults={
                'nome': 'Fernando Vier (Analista DataOps)',
                'setor_atual': 'Transformação Digital',
                'cota_total_gb': 100.00,
                'cota_used_gb': 12.40,
                'status': 'Ativo',
                'mfa_ativo': True,
                'ultimo_login': timezone.now() - timedelta(minutes=15)
            }
        )

        u_presidencia, _ = UsuarioDataOps.objects.get_or_create(
            email='ananery@cdc.org.br',
            defaults={
                'nome': 'Ana Nery (Presidenta)',
                'setor_atual': 'Presidência',
                'cota_total_gb': 100.00,
                'cota_used_gb': 8.50,
                'status': 'Ativo',
                'mfa_ativo': True,
                'ultimo_login': timezone.now() - timedelta(hours=2)
            }
        )

        u_adriana, _ = UsuarioDataOps.objects.get_or_create(
            email='adrianasantos@cdc.org.br',
            defaults={
                'nome': 'Adriana Santos',
                'setor_atual': 'Coordenação Institucional',
                'cota_total_gb': 50.00,
                'cota_used_gb': 48.07,
                'status': 'Ativo',
                'mfa_ativo': True,
                'ultimo_login': timezone.now() - timedelta(hours=1)
            }
        )

        u_joab, _ = UsuarioDataOps.objects.get_or_create(
            email='joabsilva@cdc.org.br',
            defaults={
                'nome': 'Joab da Silva (Ex-Colaborador)',
                'setor_atual': 'Atitude (Encerrado)',
                'cota_total_gb': 50.00,
                'cota_used_gb': 14.20,
                'status': 'Suspenso',
                'mfa_ativo': False,
                'ultimo_login': timezone.now() - timedelta(days=120)
            }
        )

        u_paterson, _ = UsuarioDataOps.objects.get_or_create(
            email='paterson.silva@cdc.org.br',
            defaults={
                'nome': 'Paterson Silva (Alias Projetos)',
                'setor_atual': 'Projetos',
                'cota_total_gb': 50.00,
                'cota_used_gb': 0.00,
                'status': 'Alias',
                'mfa_ativo': False,
                'ultimo_login': timezone.now() - timedelta(days=180)
            }
        )

        UsuarioDataOps.objects.get_or_create(
            email='cecilia.lima@cdc.org.br',
            defaults={
                'nome': 'Cecília Lima',
                'setor_atual': 'Administrativo Legado',
                'cota_total_gb': 50.00,
                'cota_used_gb': 22.10,
                'status': 'Inativo',
                'mfa_ativo': False,
                'ultimo_login': timezone.now() - timedelta(days=110)
            }
        )

        UsuarioDataOps.objects.get_or_create(
            email='hamilton.costa@cdc.org.br',
            defaults={
                'nome': 'Hamilton Costa',
                'setor_atual': 'Projetos',
                'cota_total_gb': 50.00,
                'cota_used_gb': 31.40,
                'status': 'Inativo',
                'mfa_ativo': False,
                'ultimo_login': timezone.now() - timedelta(days=95)
            }
        )

        UsuarioDataOps.objects.get_or_create(
            email='voluntario.marcos@cdc.org.br',
            defaults={
                'nome': 'Marcos Silva (Voluntário)',
                'setor_atual': 'Mutirão Fiscal',
                'cota_total_gb': 10.00,
                'cota_used_gb': 2.10,
                'status': 'Voluntário',
                'e_voluntario': True,
                'data_expiracao': date.today() + timedelta(days=5),
                'mfa_ativo': True,
                'ultimo_login': timezone.now() - timedelta(hours=5)
            }
        )

        # 2. Estruturas da VPN Institucional
        # Setores da Sede (Azul)
        EstruturaVpn.objects.get_or_create(
            nome='ADM',
            defaults={'tipo': 'sede', 'pcs_sede': 3, 'dispositivos_moveis': 0, 'status': 'Online', 'ip_faixa': '10.8.10.x', 'latencia': '10ms'}
        )
        EstruturaVpn.objects.get_or_create(
            nome='Financeiro',
            defaults={'tipo': 'sede', 'pcs_sede': 2, 'dispositivos_moveis': 0, 'status': 'Online', 'ip_faixa': '10.8.11.x', 'latencia': '12ms'}
        )
        EstruturaVpn.objects.get_or_create(
            nome='RH',
            defaults={'tipo': 'sede', 'pcs_sede': 2, 'dispositivos_moveis': 0, 'status': 'Online', 'ip_faixa': '10.8.12.x', 'latencia': '14ms'}
        )

        # Projetos de Proteção à Vida (Verde)
        EstruturaVpn.objects.get_or_create(
            nome='PPCAM',
            defaults={'tipo': 'projeto', 'pcs_sede': 1, 'dispositivos_moveis': 3, 'status': 'Online', 'ip_faixa': '10.8.20.x', 'latencia': '16ms'}
        )
        EstruturaVpn.objects.get_or_create(
            nome='PROVITA',
            defaults={'tipo': 'projeto', 'pcs_sede': 1, 'dispositivos_moveis': 4, 'status': 'Online', 'ip_faixa': '10.8.21.x', 'latencia': '12ms'}
        )
        EstruturaVpn.objects.get_or_create(
            nome='PPDDH',
            defaults={'tipo': 'projeto', 'pcs_sede': 1, 'dispositivos_moveis': 3, 'status': 'Online', 'ip_faixa': '10.8.22.x', 'latencia': '15ms'}
        )

        # 3. Grupos do Workspace
        g_atitude, _ = GrupoWorkspace.objects.get_or_create(
            email_grupo='equipeatitude@cdc.org.br',
            defaults={
                'nome_grupo': 'Equipe Projeto ATITUDE',
                'descricao': 'Grupo de disparo de e-mails para voluntários e equipe do projeto Atitude'
            }
        )

        g_notafiscal, _ = GrupoWorkspace.objects.get_or_create(
            email_grupo='notafiscal_adm@cdc.org.br',
            defaults={
                'nome_grupo': 'Grupo Temporário Nota Fiscal',
                'descricao': 'Grupo emergencial para arrecadação de notas fiscais de convênios'
            }
        )

        g_projetos, _ = GrupoWorkspace.objects.get_or_create(
            email_grupo='projetos@cdc.org.br',
            defaults={
                'nome_grupo': 'Setor de Projetos do CDC',
                'descricao': 'Caixa postal central do setor de Projetos'
            }
        )

        # 4. Vínculos de Grupos
        MembroGrupo.objects.get_or_create(grupo=g_atitude, usuario=u_adriana)
        MembroGrupo.objects.get_or_create(grupo=g_atitude, usuario=u_joab)
        MembroGrupo.objects.get_or_create(grupo=g_projetos, usuario=u_admin)
        MembroGrupo.objects.get_or_create(grupo=g_notafiscal, usuario=u_adriana)

        # 5. Logs de Auditoria Iniciais
        LogAuditoria.objects.get_or_create(
            acao_executada='CONVERSAO_ALIAS',
            alvo_impactado='paterson.silva@cdc.org.br',
            defaults={
                'usuario_executor': u_admin,
                'nivel': 'SUCCESS',
                'detalhes': 'Conta de ex-colaborador migrada e convertida em Apelido (Alias) do setor de Projetos (projetos@cdc.org.br). Licença liberada.',
                'ip_origem': '127.0.0.1'
            }
        )

        self.stdout.write(self.style.SUCCESS('Carga do cenário hipotético DataOps e estruturas VPN concluída com sucesso!'))
