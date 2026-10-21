# Feature Specification: Entrada (M2)

**Feature Branch**: `002-entrada` · **Created**: 2026-10-21 · **Status**: Implementada

## Contexto
A Entrada é por onde todo paciente chega ao hospital. O atendente identifica o paciente e abre o
atendimento; quem chega como paciente novo passa pela triagem (técnico de enfermagem ou enfermeiro)
e pela consulta (médico). Quem chega transferido vai direto para o destino escolhido: Ambulatório,
Enfermaria, Exame de apoio diagnóstico ou Telemedicina. Esta spec cria o paciente, o atendimento
(`CareSession`) e sua máquina de estados, a triagem, a consulta com prescrição e exames, e a etapa
de encerramento (receita e atestado) usada na alta. As specs 003 a 005 reutilizam essa etapa.

## User Scenarios & Testing

### User Story 1 - Identificar o paciente sem redigitar (Priority: P1)
Como atendente, quero achar o paciente pelo CNS, CPF ou nome e mãe, para abrir o atendimento sem
cadastrar de novo quem já veio antes.

**Acceptance Scenarios**:
1. **Dado** um CNS já cadastrado, **quando** o atendente o pesquisa, **então** o paciente aparece e,
   ao escolhê-lo, o formulário do atendimento vem com os dados dele preenchidos; nenhum paciente
   novo é criado.
2. **Dado** um CPF ou CNS com dígito errado, **quando** o atendente salva o cadastro, **então** o
   sistema recusa e diz qual campo está errado.
3. **Dado** um CNS ou CPF que já pertence a outro paciente, **quando** o atendente cadastra um
   paciente novo com ele, **então** o sistema recusa e oferece abrir o cadastro existente.
4. **Dado** uma pesquisa por parte do nome e da mãe, sem acento ou com acento, **quando** o
   atendente pesquisa, **então** os pacientes que batem aparecem.
5. **Dado** um paciente com atendimento ainda aberto, **quando** o atendente tenta abrir outro,
   **então** o sistema recusa e mostra em que etapa está o atendimento aberto.

### User Story 2 - Abrir o atendimento de paciente novo (Priority: P1)
Como atendente, quero registrar data, hora e relato da chegada, para que o paciente entre na fila
da triagem.

**Acceptance Scenarios**:
1. **Dado** um paciente identificado e origem "novo", **quando** o atendente salva, **então** o
   atendimento fica "aguardando triagem" e aparece na fila da triagem.
2. **Dado** uma data e hora de chegada no futuro, **quando** o atendente salva, **então** o sistema
   recusa.

### User Story 3 - Triagem (Priority: P1)
Como técnico de enfermagem ou enfermeiro, quero registrar sinais vitais, alergias e risco, para que
o médico atenda primeiro quem está mais grave.

**Acceptance Scenarios**:
1. **Dado** um atendimento aguardando triagem, **quando** a triagem é salva com PA, temperatura, FC,
   SpO2, alergias e classificação de risco, **então** o atendimento fica "aguardando consulta".
2. **Dado** valores fora da faixa possível (ex.: SpO2 120%, PA sistólica menor que a diastólica),
   **quando** salva, **então** o sistema recusa.
3. **Dados** dois atendimentos aguardando consulta, um de risco alto e outro de risco baixo que
   chegou antes, **quando** o médico abre a fila, **então** o de risco alto vem primeiro.

### User Story 4 - Consulta e encaminhamento (Priority: P1)
Como médico, quero registrar diagnóstico com CID-10, plano de cuidado, prescrição e exames e
encaminhar o paciente, para que a próxima equipe saiba o que fazer.

**Acceptance Scenarios**:
1. **Dado** um atendimento sem triagem, **quando** o médico tenta abrir a consulta, **então** o
   sistema bloqueia.
2. **Dado** o encaminhamento "Enfermaria", **quando** a consulta é salva, **então** o atendimento
   fica "aguardando admissão" e aparece na fila de admissão da Enfermaria.
3. **Dado** o encaminhamento "Ambulatório", **quando** a consulta é salva, **então** o atendimento
   aparece na fila do Ambulatório.
4. **Dada** uma prescrição, **quando** a consulta é salva, **então** cada medicamento fica com
   dosagem, forma, via e posologia (vezes, intervalo de 6/8/12/24 h, duração e unidade), e cada
   exame fica ligado ao tipo de exame cadastrado.
5. **Dado** um CID-10 que não existe na tabela importada, **quando** salva, **então** o sistema
   recusa.

### User Story 5 - Alta na consulta com receita e atestado (Priority: P1)
Como médico, quero dar alta direto da consulta e entregar receita e atestado impressos.

**Acceptance Scenarios**:
1. **Dado** o encaminhamento "Alta", **quando** a consulta é salva, **então** o atendimento fica
   "finalizado", com data e hora de saída, e não aceita mais alterações.
2. **Dada** uma alta com atestado de N dias, **quando** a consulta é salva, **então** o atestado
   fica registrado (dias, CID opcional, médico, data) e pode ser impresso.
3. **Dada** uma alta com medicamentos prescritos, **quando** o médico pede a receita, **então** a
   receita sai com os medicamentos e a posologia, pronta para impressão, com espaço para
   assinatura e carimbo.
4. **Dado** um atendimento que não teve alta, **quando** alguém pede a receita ou o atestado,
   **então** o sistema recusa.

### User Story 6 - Paciente transferido (Priority: P2)
Como atendente, quero registrar a chegada de um paciente transferido e mandá-lo direto ao destino.

**Acceptance Scenarios**:
1. **Dado** origem "transferência" e destino "Enfermaria", **quando** o atendente salva com médico
   responsável e diagnóstico da guia, **então** o atendimento vai direto para a fila de admissão,
   sem triagem nem consulta.
2. **Dado** destino "Ambulatório", **quando** salva, **então** o atendimento vai para a fila do
   Ambulatório.
3. **Dado** destino "Exame de apoio diagnóstico", **quando** o atendente salva com os exames
   pedidos, **então** os pedidos ficam registrados com campo para o identificador do LabSUS, a tela
   mostra o link do LabSUS e o atendimento é finalizado.
4. **Dado** destino "Telemedicina", **quando** o atendente salva com as datas e quantidades,
   **então** elas ficam registradas e o atendimento é finalizado.
5. **Dado** um atendimento de transferência, **quando** alguém tenta registrar triagem ou consulta
   nele, **então** o sistema recusa.

### Máquina de estados

| De | Evento | Para |
| --- | --- | --- |
| (novo) | abrir, origem novo | `awaiting_triage` |
| (novo) | abrir, transferência para Ambulatório | `ambulatory` |
| (novo) | abrir, transferência para Enfermaria | `awaiting_admission` |
| (novo) | abrir, transferência para Exame ou Telemedicina | `finished` |
| `awaiting_triage` | salvar triagem | `awaiting_consultation` |
| `awaiting_consultation` | consulta com encaminhamento Ambulatório | `ambulatory` |
| `awaiting_consultation` | consulta com encaminhamento Enfermaria | `awaiting_admission` |
| `awaiting_consultation` | consulta com alta | `finished` |

Qualquer outra transição é recusada pelo service. `ambulatory` e `awaiting_admission` seguem nas
specs 003 e 004.

### Edge Cases
- Dois atendentes salvando o mesmo paciente novo ao mesmo tempo: a chave única de CNS e CPF no
  banco impede o duplicado; o segundo recebe a mensagem de paciente já cadastrado.
- Dois profissionais salvando a triagem do mesmo atendimento: o segundo recebe "triagem já
  registrada".
- Paciente sem CNS: pode ser cadastrado com CPF, e vice-versa; sem nenhum dos dois, não.
- Paciente sem número de prontuário: o sistema gera o próximo número livre.

## Requirements

- **FR-001**: Paciente com CNS e CPF únicos quando informados (pelo menos um dos dois), prontuário
  único, nome, nome da mãe, sexo, raça/cor, nascimento, telefone, endereço com município IBGE e
  CEP. Sexo e raça/cor usam os códigos do SUS.
- **FR-002**: Busca por CNS ou CPF (com ou sem máscara) ou por nome e mãe, sem diferenciar acento
  nem maiúsculas.
- **FR-003**: Um paciente tem no máximo um atendimento aberto (regra no banco).
- **FR-004**: Toda mudança de status passa pelo service da tabela acima; o resto é recusado.
- **FR-005**: Triagem e consulta são 1:1 com o atendimento e guardam quem registrou e quando.
- **FR-006**: Medicamentos e tipos de exame vêm de catálogos cadastrados pelo admin; o catálogo de
  exames já nasce com os sete do template (Hemograma, Glicemia, Ureia, Creatinina, Colesterol,
  Raio-X de Tórax, ECG).
- **FR-007**: Pedido de exame tem campo para o identificador externo do LabSUS; o link do LabSUS
  vem da variável de ambiente `LABSUS_URL`.
- **FR-008**: Atendimento finalizado é só leitura: o service recusa qualquer escrita nele.
- **FR-009**: Abrir a triagem ou a consulta de um paciente grava um registro de acesso (usuário,
  paciente, atendimento, data e hora), como ficou combinado na spec 001.
- **FR-010**: Telas em português, baseadas em `identification.html`, `triage.html` e
  `consult.html`, sem JavaScript próprio além de adicionar linha de medicamento e exame.

## Clarifications
### Session 2026-10-21
Decisões tomadas para não travar a spec, a confirmar com o Victor:
- Sexo só M ou F, como pede o Laudo de AIH; o "Outro" do template sai.
- Raça/cor com os códigos do SUS: 01 Branca, 02 Preta, 03 Parda, 04 Amarela, 05 Indígena,
  99 Sem informação.
- Paciente precisa de CNS ou CPF. Paciente sem documento nenhum fica fora desta spec.
- Receita e atestado abrem numa página pronta para impressão (o navegador salva em PDF). O PDF
  gerado no servidor, com WeasyPrint, entra no M6 junto com os outros documentos.
- Transferência para Exame ou Telemedicina finaliza o atendimento no próprio registro, porque não
  há etapa seguinte dentro do hospital.
- Na transferência para Ambulatório ou Enfermaria, o atendente transcreve da guia o médico
  responsável, o diagnóstico (CID-10), o plano, a prescrição e os exames, como no template de
  identificação.
- Telas sempre em português, mesmo em navegador em inglês (sai o `LocaleMiddleware`; antes a data
  da receita saía como "October").
- Tipo de logradouro como texto (Rua, Avenida, Travessa...). O código DNE que o SISAIH01 pede fica
  para o M6.

## Fora de escopo
Fila e procedimentos do Ambulatório (spec 003), admissão (spec 004), evoluções e alta da
enfermaria (spec 005), PDFs de servidor e Finalizados (spec 006), integração real com o LabSUS,
paciente sem documento, edição do cadastro do paciente fora da Entrada.
