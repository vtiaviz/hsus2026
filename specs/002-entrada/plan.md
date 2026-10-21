# Implementation Plan: Entrada (M2)

**Spec**: [spec.md](spec.md) · **Data model**: [data-model.md](data-model.md)

## Technical Context
- Dois apps novos previstos no PRD: `patients` (paciente e registro de acesso) e `clinical`
  (catálogos, prescrição, pedido de exame e atestado, que as specs 003 a 005 reutilizam).
- `reception` ganha o atendimento (`CareSession`), a triagem, a consulta e o registro de
  telemedicina. A máquina de estados fica em `apps/reception/services.py`: cada transição é uma
  função, e `ensure_status()` recusa qualquer outra.
- Busca sem acento com a extensão `unaccent` do PostgreSQL (`django.contrib.postgres`), ativada por
  migração.
- Um atendimento aberto por paciente: `UniqueConstraint(fields=["patient"],
  condition=~Q(status="finished"))`.
- Paciente com CNS ou CPF: `CheckConstraint`; os dois são `unique` e `null` quando vazios.
- Prontuário gerado pelo service quando vem vazio: próximo número numérico livre, dentro da mesma
  transação do cadastro.
- Formulários: `ModelForm` por etapa e formsets para medicamentos, exames e telemedicina. Um
  script de 20 linhas em `static/js/formset.js` adiciona linhas ao formset; o resto é HTML
  renderizado no servidor.
- Receita e atestado: templates de impressão sem barra lateral, com `@media print`, a partir de
  `consult.html` e `atestado.html`.
- Filas: selectors em `apps/reception/selectors.py`; a da consulta ordena por risco (muito alta
  primeiro) e depois por chegada.
- As páginas de Ambulatório (procedimentos) e Enfermaria (admissão) passam a listar sua fila,
  para os critérios de aceite de encaminhamento. O resto delas vem nas specs 003 e 004.
- `LABSUS_URL` como variável de ambiente, com padrão vazio (o link some se não houver valor).

## Constitution Check
| Princípio | Como o M2 atende |
| --- | --- |
| I Simplicidade | Nenhuma dependência nova; `unaccent` já vem com o PostgreSQL |
| II Testes | Cada cenário de aceite tem teste; services e selectors com teste unitário |
| III Camadas | Views só chamam forms, services e selectors |
| IV Atendimento no centro | Status só muda pelas funções de transição do service |
| V Nada clínico é apagado | FKs `PROTECT`; atendimento finalizado recusa escrita |
| VI Rastreabilidade | `created_by`/`recorded_by` e horário em todo registro; log de acesso |
| VII Permissão | Views com `required_action`; matriz da spec 001 sem mudança |
| VIII Códigos oficiais | CID-10 por FK; sexo e raça/cor com códigos do SUS |

## Complexity Tracking
Nenhuma exceção.
