# H-SUS

Gestão de atendimentos para hospitais de pequeno porte do SUS: entrada, triagem, consulta,
ambulatório, enfermaria e emissão de Laudo de AIH, AIH, prontuário e evoluções.

Desenvolvido com *spec driven development* ([Spec Kit](https://github.com/github/spec-kit)):
constituição em `.specify/memory/constitution.md` e uma pasta por milestone em `specs/`.

## Rodando localmente

```bash
cp .env.example .env
docker compose up            # http://localhost:8000/health/
```

Para acessar por outro endereço (por exemplo, o IP de uma VM), adicione-o em `ALLOWED_HOSTS` no
`.env`, separado por vírgulas: `ALLOWED_HOSTS=localhost,127.0.0.1,192.168.56.20`.

Sem Docker para a aplicação (só o banco):

```bash
docker compose up -d db
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

## Tabelas oficiais

```bash
uv run python manage.py import_discharge_reasons data/motivos_saida_sih.csv
uv run python manage.py import_municipalities data/municipios_ibge.csv
uv run python manage.py import_cid10 CID-10-SUBCATEGORIAS.CSV
uv run python manage.py import_sigtap TabelaUnificada_AAAAMM/tb_procedimento.txt
uv run python manage.py import_cbo "CBO2002 - Ocupacao.csv"
```

Formatos e fontes em [`data/README.md`](data/README.md).

## Milestones

| # | Spec | Situação |
| --- | --- | --- |
| M0 | Fundação | Implementada |
| M1 | Autenticação e perfis | — |
| M2 | Entrada (identificação, triagem, consulta) | — |
| M3 | Ambulatório | — |
| M4 | Admissão na enfermaria | — |
| M5 | Evoluções médica e de enfermagem | — |
| M6 | Finalizados, documentos, AIH e API do bot | — |
