# Feature Specification: Autenticação e perfis (M1)

**Feature Branch**: `001-autenticacao-perfis` · **Created**: 2026-10-21 · **Status**: Em revisão

## Contexto
O H-SUS é usado por cinco perfis: administrador, atendente, técnico de enfermagem, enfermeiro e
médico. Cada um só pode ver e fazer o que corresponde à sua função. Esta spec entrega o login, os
perfis, a barra lateral (Entrada, Ambulatório, Enfermaria, Finalizados) e a regra que libera ou nega
cada área. As telas de cada área ainda são páginas vazias; o conteúdo vem nas specs 002 a 006.

## User Scenarios & Testing

### User Story 1 - Entrar e sair do sistema (Priority: P1)
Como profissional, quero entrar com meu usuário e senha e sair quando terminar, para que ninguém use
o sistema no meu nome.

**Acceptance Scenarios**:
1. **Dado** um usuário ativo com senha correta, **quando** faz login, **então** cai na página
   inicial com a barra lateral do seu perfil.
2. **Dado** um usuário inativo, **quando** tenta entrar, **então** o login é recusado com a mesma
   mensagem de senha errada (sem revelar que o usuário existe).
3. **Dado** um visitante sem login, **quando** abre qualquer página do sistema (exceto login e
   `/health/`), **então** é levado ao login e, depois de entrar, volta para a página pedida.
4. **Dado** um usuário logado, **quando** clica em Sair, **então** a sessão termina e voltar no
   navegador não mostra dados.
5. **Dado** um usuário parado por 30 minutos, **quando** clica em qualquer link, **então** precisa
   entrar de novo.

### User Story 2 - Bloqueio por tentativas (Priority: P1)
Como administrador, quero que o sistema bloqueie quem erra a senha muitas vezes, para dificultar a
adivinhação de senhas.

**Acceptance Scenarios**:
1. **Dado** 5 tentativas erradas para o mesmo usuário em 15 minutos, **quando** tenta de novo,
   **então** o acesso fica bloqueado por 15 minutos, mesmo com a senha certa, e a tela explica o
   bloqueio.
2. **Dado** um usuário bloqueado, **quando** o administrador o desbloqueia no painel, **então** ele
   pode entrar imediatamente.

### User Story 3 - Perfis e áreas permitidas (Priority: P1)
Como administrador, quero atribuir um perfil a cada usuário, para que cada um veja só as áreas da
sua função.

**Acceptance Scenarios**:
1. **Dado** um atendente logado, **quando** abre a URL da evolução médica, **então** recebe 403 com
   uma página em português.
2. **Dado** um usuário de qualquer perfil, **quando** vê a barra lateral, **então** ela mostra só as
   áreas em que ele tem pelo menos uma ação permitida.
3. **Dado** um usuário com dois perfis (ex.: enfermeiro e administrador), **quando** acessa o
   sistema, **então** tem a soma das permissões dos dois.
4. **Dado** um usuário sem perfil, **quando** entra, **então** vê a página inicial com o aviso
   "Seu usuário ainda não tem perfil; procure o administrador" e nenhuma área.
5. **Dada** a matriz abaixo, **quando** os testes rodam, **então** cada célula (perfil × ação) é
   verificada automaticamente contra a URL correspondente.

### Matriz de perfis

| Área / ação | Admin | Atendente | Técnico | Enfermeiro | Médico |
| --- | --- | --- | --- | --- | --- |
| Entrada: identificação | sim | sim | não | não | não |
| Entrada: triagem | sim | não | sim | sim | não |
| Entrada: consulta | sim | não | não | não | sim |
| Ambulatório: procedimentos | sim | não | sim | sim | sim |
| Enfermaria: admissão | sim | não | não | sim | não |
| Enfermaria: evolução de enfermagem | sim | não | sim | sim [NEEDS CLARIFICATION] | não |
| Enfermaria: evolução médica e alta | sim | não | não | não | sim |
| Finalizados: ver e imprimir | sim | sim | não | não | sim |
| Painel de administração | sim | não | não | não | não |

### Edge Cases
- Usuário com `is_superuser` tem todas as permissões, mesmo sem perfil.
- Nome de usuário não diferencia maiúsculas de minúsculas no login.
- Remover o perfil de alguém logado vale na próxima página que ele abrir.

## Requirements

- **FR-001**: Cinco perfis criados por migração, com nomes fixos no código: `admin`, `attendant`,
  `nursing_technician`, `nurse`, `physician` (rótulos em português na tela).
- **FR-002**: Cada ação da matriz é uma constante em código; a matriz é a única fonte da verdade
  para views, barra lateral e testes.
- **FR-003**: Toda view, exceto login, logout e `/health/`, exige login; as views de área exigem a
  ação correspondente (padrão: negar).
- **FR-004**: Bloqueio após 5 falhas em 15 minutos por nome de usuário; desbloqueio pelo admin.
- **FR-005**: Telas de login, 403 e 404 em português, sobre `base.html`.
- **FR-006**: O admin do Django mostra e permite trocar o perfil no cadastro do usuário.

## Clarifications
- [NEEDS CLARIFICATION] O enfermeiro também registra evolução de enfermagem, ou só o técnico?
  (O rascunho libera para os dois.)

## Fora de escopo
Troca de senha pelo próprio usuário e recuperação por e-mail (a senha é redefinida pelo admin),
login com certificado digital, log de acesso a prontuário (entra com o primeiro prontuário, no M2).
