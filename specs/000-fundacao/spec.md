# Feature Specification: Fundação do projeto (M0)

**Feature Branch**: `000-fundacao` · **Created**: 2026-10-20 · **Status**: Implementada

## User Scenarios & Testing

### User Story 1 - Ambiente reproduzível (Priority: P1)
Como desenvolvedor, quero subir o sistema e rodar os testes com um comando, para trabalhar com o
agente de IA sem configurar nada à mão.

**Acceptance Scenarios**:
1. **Dado** um clone limpo, **quando** rodo `docker compose up`, **então** a aplicação responde em
   `/health/` com `{"status": "ok"}` usando PostgreSQL 16.
2. **Dado** um PR aberto, **quando** o CI roda, **então** lint, checagem de migrações, testes e
   cobertura mínima de 85% passam ou o PR fica vermelho.

### User Story 2 - Estrutura do hospital (Priority: P1)
Como administrador, quero cadastrar o estabelecimento, suas alas e leitos, para que os documentos
usem esses dados em vez de valores fixos no HTML.

**Acceptance Scenarios**:
1. **Dado** um CNES já cadastrado, **quando** cadastro outro estabelecimento com o mesmo CNES,
   **então** o sistema recusa.
2. **Dado** uma ala com o leito 01, **quando** cadastro outro leito 01 na mesma ala, **então** o
   sistema recusa; em outra ala é permitido.
3. **Dada** uma ala com leitos, **quando** tento excluí-la, **então** o sistema recusa.

### User Story 3 - Tabelas oficiais (Priority: P1)
Como administrador, quero importar CID-10, SIGTAP, CBO, municípios IBGE e motivos de saída do SIH a
partir dos arquivos oficiais.

**Acceptance Scenarios**:
1. **Dado** o arquivo do CID-10, **quando** rodo a importação duas vezes, **então** não há
   duplicados e descrições alteradas são atualizadas.
2. **Dado** o `tb_procedimento.txt` do SIGTAP, **quando** importo, **então** o código mantém o zero
   inicial (ex.: `0303010037`) e a competência é registrada.
3. **Dado** um arquivo sem as colunas esperadas, **quando** importo, **então** o comando falha com
   mensagem clara e nada é gravado.
4. **Dado** o painel de administração, **quando** abro uma tabela oficial, **então** ela é só
   leitura.

### Edge Cases
- Arquivos oficiais em Latin-1 (DATASUS) e UTF-8.
- Código IBGE com 6 dígitos (formato SUS) é recusado na importação; o model guarda 7 e expõe
  `sus_code` com 6.

## Requirements

- **FR-001**: Usuário customizado (`core.User`) com nome completo, CPF, CNS, CBO, registro no
  conselho e estabelecimento.
- **FR-002**: CPF e CNS validados pelo dígito verificador.
- **FR-003**: `Establishment`, `Ward` e `Bed` com `PROTECT`; ala e leito apontam para o
  estabelecimento (preparação para vários hospitais).
- **FR-004**: Comandos `import_cid10`, `import_sigtap`, `import_cbo`, `import_municipalities`,
  `import_discharge_reasons`, idempotentes.
- **FR-005**: Configuração por variáveis de ambiente; fuso `America/Belem`; idioma pt-BR; sessão
  expira após 30 minutos sem uso; senha mínima de 10 caracteres.

## Fora de escopo
Perfis e permissões (M1), tipos de logradouro (M2), auditoria com histórico (entra junto do primeiro
model clínico, no M2).

## Pendências
- [NEEDS CLARIFICATION] Conferir `data/motivos_saida_sih.csv` contra a tabela oficial do SIH.
