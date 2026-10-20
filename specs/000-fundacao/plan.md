# Implementation Plan: Fundação do projeto (M0)

**Spec**: [spec.md](spec.md)

## Technical Context
- Python 3.12, Django 5.2 LTS, PostgreSQL 16, psycopg 3, django-environ
- Testes: pytest-django, factory-boy, coverage (mínimo 85%)
- Qualidade: ruff (lint + format)
- Execução: Docker Compose (db + web), Gunicorn em produção
- Gerenciador de dependências: uv (`uv.lock` versionado)

## Constitution Check
| Princípio | Como o M0 atende |
| --- | --- |
| I Simplicidade | Um app (`core`), sem dependências além do necessário |
| II Testes | 40 testes, cobertura 99% |
| III Camadas | Importações em `services.py`; comandos só chamam o service |
| V Nada apagado | `on_delete=PROTECT` em todas as FKs |
| VIII Códigos oficiais | Códigos como texto, chave primária pelo código oficial |
| X LGPD | `.gitignore` bloqueia `*.sql`; factories geram CPF/CNS fictícios válidos |

## Project Structure
```
config/settings/{base,dev,test,prod}.py
apps/core/{models,services,validators,views,admin,urls}.py
apps/core/management/commands/import_*.py
apps/core/tests/
data/motivos_saida_sih.csv
templates/base.html
```

## Complexity Tracking
Nenhuma exceção.
