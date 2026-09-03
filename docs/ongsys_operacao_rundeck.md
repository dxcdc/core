# Operação da integração OngSys pelo Rundeck

Este documento define o contrato do CDC Core com o executor institucional. Ele
não autoriza publicação nem altera o Rundeck.

## Pré-requisitos

- migrations do app `integrations` aplicadas até `0007_ongsy_task`;
- credencial fora do Git em `/etc/cdc/secrets/ongsys.env` ou em variáveis de
  ambiente do processo;
- usuário executor com acesso ao mesmo ambiente e banco do CDC Core;
- lock, timeout, ACL, backup restaurável e rollback homologados no Rundeck.

O arquivo de segredo aceita `ONGSYS_USERNAME` ou `ONGSYS_CNPJ`,
`ONGSYS_PASSWORD` ou `ONGSYS_API_KEY`, e `ONGSYS_BASE_URL` ou
`ONGSYS_URL_BASE`. Valores nunca devem aparecer em argumentos, logs ou Git.

## Comando do executor

Executar dentro do ambiente da aplicação:

```text
python manage.py process_ongsys_task --max-tasks 10
```

O lote é limitado entre 1 e 100 tarefas. Para uma tarefa explicitamente
selecionada:

```text
python manage.py process_ongsys_task --task-id UUID
```

`--task-id` não pode ser combinado com `--max-tasks` diferente de 1.

## Semântica de retorno

- fila vazia: saída normal, sem trabalho;
- todas concluídas: código de saída zero;
- qualquer tarefa parcial ou com erro: código de saída diferente de zero;
- cada linha informa somente `task_id` e `status`, sem credenciais ou payloads.

O job deve ser serializado pelo lock institucional. Uma nova execução não
deve contornar tarefas marcadas como `running`.

## Permissões da interface

- observador: `integrations.view_ongsysendpointstatus`;
- operador de testes: `integrations.test_ongsys_api`;
- operador de sincronização: `integrations.sync_ongsys_data`;
- leitor de relatórios: `integrations.view_ongsys_report`.

Conceder somente as permissões necessárias por grupo. Superusuário não deve
ser requisito operacional.

## Critérios de homologação

1. `python manage.py check` sem erros no mesmo ambiente do executor.
2. Migrações confirmadas no banco efetivamente usado pelo Core.
3. Tarefa de teste criada na interface permanece `queued` até o Rundeck agir.
4. Rundeck assume a tarefa uma única vez e persiste progresso e resultado.
5. Falha do provedor produz estado `partial` ou `error` e alerta do job.
6. Relatório mostra o último teste persistido, sem inferir disponibilidade.
7. Backup pré-deploy restaurado em ambiente isolado e rollback ensaiado.
8. Após o deploy, validação autenticada da rota e das quatro permissões.

## Ordem de publicação

Backup restaurável, preflight, migrations, aplicação, configuração do job,
teste controlado, validação autenticada e registro das evidências. O deploy é
a última etapa e exige autorização separada.
