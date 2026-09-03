from django.core.management.base import BaseCommand, CommandError

from apps.integrations.ongsys_tasks import claim_task, process_claimed_task


class Command(BaseCommand):
    help = "Processa uma tarefa OngSys persistida; executor previsto: Rundeck."

    def add_arguments(self, parser):
        parser.add_argument("--task-id", help="UUID específico; sem ele, processa a próxima tarefa.")
        parser.add_argument(
            "--max-tasks",
            type=int,
            default=1,
            help="Quantidade máxima de tarefas da fila a processar (1 a 100).",
        )

    def handle(self, *args, **options):
        task_id = options.get("task_id")
        max_tasks = options["max_tasks"]
        if not 1 <= max_tasks <= 100:
            raise CommandError("--max-tasks deve estar entre 1 e 100.")
        if task_id and max_tasks != 1:
            raise CommandError("--task-id não pode ser combinado com --max-tasks diferente de 1.")

        processed = []
        failures = []
        for _ in range(max_tasks):
            task = claim_task(task_id)
            if not task:
                break
            result = process_claimed_task(task)
            processed.append(result)
            self.stdout.write(f"task_id={result.pk} status={result.status}")
            if result.status in {"partial", "error"}:
                failures.append(result)
            if task_id:
                break

        if not processed:
            self.stdout.write("Nenhuma tarefa OngSys disponível.")
            return
        self.stdout.write(f"processed={len(processed)} failures={len(failures)}")
        if failures:
            raise CommandError("Uma ou mais tarefas OngSys foram encerradas com falhas.")
