from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from apps.dataops.models import UsuarioDataOps, GrupoWorkspace, MembroGrupo, NotaFiscalConciliacao, LogAuditoria

class Command(BaseCommand):
    help = 'Popula o banco de dados local do CDC Core com o cenário hipotético DataOps'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Inicializando carga de dados hipotéticos do CDC DataOps...'))

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

        # Caso Adriana Santos (Estouro de Cota - 48.07GB de 50GB = 96.1%)
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

        # Caso Joab da Silva (Suspenso, mas presente em grupo - Brecha de Segurança)
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

        # Caso Paterson Silva (Convertido em Alias)
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

        # Contas Inativas (> 90 dias)
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

        # Voluntário com Expiração Próxima
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

        # 2. Grupos do Workspace
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

        # 3. Vínculos de Grupos (Incluindo a brecha do Joab)
        MembroGrupo.objects.get_or_create(grupo=g_atitude, usuario=u_adriana)
        MembroGrupo.objects.get_or_create(grupo=g_atitude, usuario=u_joab)  # BRECHA!
        MembroGrupo.objects.get_or_create(grupo=g_projetos, usuario=u_admin)
        MembroGrupo.objects.get_or_create(grupo=g_notafiscal, usuario=u_adriana)

        # 4. Notas Fiscais e Conciliação
        NotaFiscalConciliacao.objects.get_or_create(
            chave_acesso='35260803970166000129550010000123451000123456',
            defaults={
                'numero_nota': '12345',
                'data_emissao': date.today() - timedelta(days=10),
                'valor': 4850.00,
                'projeto_vinculado': 'Projeto Atitude',
                'status_conciliacao': 'Pendente',
                'importado_por': u_admin
            }
        )

        NotaFiscalConciliacao.objects.get_or_create(
            chave_acesso='35260803970166000129550010000123461000654321',
            defaults={
                'numero_nota': '12346',
                'data_emissao': date.today() - timedelta(days=15),
                'valor': 12300.50,
                'projeto_vinculado': 'Convênio SEFAZ',
                'status_conciliacao': 'Conciliado',
                'importado_por': u_admin
            }
        )

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

        LogAuditoria.objects.get_or_create(
            acao_executada='ALERTA_THRESHOLD_80',
            alvo_impactado='adrianasantos@cdc.org.br',
            defaults={
                'usuario_executor': u_admin,
                'nivel': 'WARN',
                'detalhes': 'Armazenamento atingiu 48.07GB de 50GB (96.1%). Disparado alerta preventivo no WhatsApp e e-mail educacional.',
                'ip_origem': '127.0.0.1'
            }
        )

        LogAuditoria.objects.get_or_create(
            acao_executada='ALERTA_VULNERABILIDADE_GRUPO',
            alvo_impactado='joabsilva@cdc.org.br',
            defaults={
                'usuario_executor': u_admin,
                'nivel': 'ERROR',
                'detalhes': 'Conta com status Suspenso permanece vinculada como membro ativo no grupo equipeatitude@cdc.org.br. Ação imediata requerida.',
                'ip_origem': '127.0.0.1'
            }
        )

        self.stdout.write(self.style.SUCCESS('Carga do cenário hipotético DataOps concluída com sucesso!'))
