from io import StringIO
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.integrations.models import OngsysTask
from apps.integrations.ongsys_tasks import claim_task, process_claimed_task


class OngsysDurableTaskTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='task-owner')

    def test_claim_changes_queued_task_to_running_once(self):
        task = OngsysTask.objects.create(
            tipo=OngsysTask.Tipo.SYNC_DB,
            solicitante=self.user,
            entidade='fornecedores',
            paginas=1,
        )

        claimed = claim_task(task.pk)

        self.assertEqual(task.pk, claimed.pk)
        self.assertEqual(OngsysTask.Status.RUNNING, claimed.status)
        self.assertIsNone(claim_task(task.pk))

    @patch('apps.integrations.ongsys_tasks._sync_steps')
    def test_processing_persists_successful_result(self, sync_steps):
        sync_steps.return_value = [
            ('Fornecedores', Mock(return_value={
                'entidade': 'Fornecedores', 'total': 3, 'duracao': 0.1
            }))
        ]
        task = OngsysTask.objects.create(
            tipo=OngsysTask.Tipo.SYNC_DB,
            solicitante=self.user,
            entidade='fornecedores',
            paginas=1,
        )
        claimed = claim_task(task.pk)

        process_claimed_task(claimed)

        task.refresh_from_db()
        self.assertEqual(OngsysTask.Status.COMPLETED, task.status)
        self.assertEqual(100, task.progresso_pct)
        self.assertEqual(3, task.resultados[0]['total'])
        self.assertIsNotNone(task.finalizado_em)

    @patch('apps.integrations.ongsys_tasks._sync_steps')
    def test_processing_persists_partial_result(self, sync_steps):
        successful = Mock(return_value={
            'entidade': 'Fornecedores', 'total': 3, 'duracao': 0.1
        })
        failed = Mock(side_effect=RuntimeError('provider unavailable'))
        sync_steps.return_value = [
            ('Fornecedores', successful),
            ('Clientes', failed),
        ]
        task = OngsysTask.objects.create(
            tipo=OngsysTask.Tipo.SYNC_DB,
            solicitante=self.user,
            entidade='all',
            paginas=1,
        )
        claimed = claim_task(task.pk)

        process_claimed_task(claimed)

        task.refresh_from_db()
        self.assertEqual(OngsysTask.Status.PARTIAL, task.status)
        self.assertIn('provider unavailable', task.erro)

    @patch('apps.integrations.ongsys_tasks._sync_steps')
    def test_management_command_drains_a_bounded_queue(self, sync_steps):
        sync_steps.return_value = [
            ('Fornecedores', Mock(return_value={
                'entidade': 'Fornecedores', 'total': 1, 'duracao': 0.1
            }))
        ]
        for entity in ('fornecedores', 'clientes'):
            OngsysTask.objects.create(
                tipo=OngsysTask.Tipo.SYNC_DB,
                solicitante=self.user,
                entidade=entity,
                paginas=1,
            )
        stdout = StringIO()

        call_command('process_ongsys_task', max_tasks=2, stdout=stdout)

        self.assertEqual(
            2,
            OngsysTask.objects.filter(status=OngsysTask.Status.COMPLETED).count(),
        )
        self.assertIn('processed=2 failures=0', stdout.getvalue())

    def test_management_command_rejects_unbounded_batch(self):
        with self.assertRaises(CommandError):
            call_command('process_ongsys_task', max_tasks=101)
