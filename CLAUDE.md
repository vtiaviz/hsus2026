# H-SUS · instruções para o agente

Sistema de gestão de atendimentos para hospitais de pequeno porte do SUS. Leia antes de qualquer
mudança:

- `.specify/memory/constitution.md` — princípios não negociáveis.
- `specs/<NNN>/spec.md` da feature em andamento — o quê e por quê. Não implemente nada que não
  esteja na spec; se faltar algo, marque `[NEEDS CLARIFICATION]` e pergunte.

## Comandos
```bash
uv sync                                   # dependências
docker compose up -d db                   # PostgreSQL 16 local
uv run python manage.py migrate
uv run pytest                             # testes
uv run coverage run -m pytest && uv run coverage report   # cobertura (mínimo 85%)
uv run ruff check . && uv run ruff format .                # lint e formatação
uv run python manage.py makemigrations --check --dry-run   # migrações em dia
```

## Regras de código
- Apps em `apps/<nome>/`; código, tabelas e URLs em inglês; textos da tela em português com
  `gettext_lazy`.
- Camadas: `views.py` orquestra, `forms.py` valida, `services.py` escreve e decide, `selectors.py`
  lê, `models.py` guarda dados e invariantes simples.
- FKs com `on_delete=models.PROTECT`. Nada clínico é apagado.
- Códigos oficiais (CID-10, SIGTAP, CBO, IBGE) são texto, nunca inteiro.
- Testes primeiro: cada critério de aceite da spec vira um teste em `apps/<nome>/tests/`.
  Use as factories de `apps/core/tests/factories.py`; nunca dados reais.
- Antes de abrir PR: testes, cobertura, ruff e checagem de migrações passando.
