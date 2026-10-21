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

## Permissões (spec 001)
- Toda view exige login (`LoginRequiredMiddleware`). Views públicas usam `@login_not_required`.
- Views de área declaram a ação: `ActionRequiredMixin` com `required_action = Action.X` (CBV) ou
  `@action_required(Action.X)` (FBV). Ações e perfis ficam só em `apps/core/permissions.py`.
- Ação nova = constante em `Action`, entrada em `ROLE_ACTIONS`, item em `navigation.SIDEBAR` e
  linha em `SPEC_MATRIX` de `test_permissions.py` (o teste perfil × ação cobre a URL sozinho).
- Em testes, use `client.force_login(user, backend=MODEL_BACKEND)` e `user_with_roles(...)` das
  factories (o primeiro backend é o do django-axes).

## Atendimento (spec 002)
- O status de `CareSession` só muda em `apps/reception/services.py` (`TRANSITIONS`,
  `apply_transition`, `ensure_status`). Etapa nova = evento novo na tabela + teste da transição
  e das recusadas.
- Services recebem instâncias ainda não salvas vindas dos forms (`form.save(commit=False)`,
  `unsaved_items(formset)`) e gravam tudo numa transação.
- Telas que abrem dados do paciente chamam `apps.patients.services.log_access`.
- Formulários: `{{ form.campo.as_field_group }}` já sai no padrão do Bootstrap
  (`BootstrapFormRenderer`); formsets com `includes/formset.html`.
- Factories de paciente e atendimento: `apps/patients/tests/factories.py` e
  `apps/reception/tests/factories.py`.
