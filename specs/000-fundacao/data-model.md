# Data Model: Fundação (M0)

| Model | Chave | Campos principais | Relações |
| --- | --- | --- | --- |
| `Municipality` | `ibge_code` (7 dígitos) | `name`, `state`; `sus_code` (6 dígitos) | — |
| `Cid10` | `code` (sem ponto, ex.: `J189`) | `description`; `formatted_code` | — |
| `SigtapProcedure` | `code` (10 dígitos) | `name`, `competence` (AAAAMM) | — |
| `Cbo` | `code` (6 dígitos) | `title` | — |
| `DischargeReason` | `code` (2 dígitos) | `description`, `kind` (alta, permanência, transferência, óbito, administrativo, parto); `ends_care` | — |
| `Establishment` | id | `name`, `cnes` (único), `issuing_body` | `Municipality` (PROTECT) |
| `Ward` | id | `name` (único por estabelecimento), `is_active` | `Establishment` (PROTECT) |
| `Bed` | id | `number` (único por ala), `is_active` | `Ward` (PROTECT) |
| `User` | id | `full_name`, `cpf`, `cns` (únicos, opcionais), `council_registry` | `Cbo`, `Establishment` (PROTECT) |
