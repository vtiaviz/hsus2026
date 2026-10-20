# Constituição do H-SUS

Versão 1.0.0 · ratificada em 2026-10-20

Princípios que valem para toda spec, plano e PR. Uma exceção precisa de justificativa escrita no
`plan.md` da feature (seção "Complexity Tracking").

## I. Simplicidade primeiro
Django puro, templates renderizados no servidor e HTMX para interações parciais. Sem SPA, sem
microsserviços, sem dependência nova sem justificativa escrita.

## II. Testes como contrato
Todo critério de aceite tem pelo menos um teste automatizado. Services e selectors têm teste
unitário; views têm teste de permissão. Cobertura mínima de 85% nos apps de domínio (o CI falha
abaixo disso).

## III. Camadas com papel único
A view orquestra; o form valida a entrada; o service escreve e aplica regra de negócio; o selector
lê com consultas complexas; o model guarda dados e invariantes simples. A view nunca chama
`.save()` de domínio diretamente.

## IV. O atendimento é o centro
Todo registro clínico pertence a um atendimento (`CareSession`). O status do atendimento muda apenas
por transições explícitas no service, que rejeita transições inválidas.

## V. Nada clínico é apagado
Registros clínicos não têm exclusão física nem `CASCADE` (`on_delete=PROTECT`). Correções geram nova
versão ou cancelamento com motivo, autor e data. Após a alta, o atendimento fica só leitura.

## VI. Rastreabilidade
Toda escrita registra quem fez e quando. Acesso a prontuário fica em log de auditoria.

## VII. Permissão por perfil, testada
Cada view declara o perfil exigido; o padrão é negar acesso. A matriz de perfis tem teste
automático.

## VIII. Códigos oficiais, não texto livre
CID-10, procedimento SIGTAP, CBO, município IBGE, raça/cor, sexo e motivo de saída usam tabelas de
referência ou `TextChoices` com o código oficial. Códigos são texto (preservam zeros à esquerda).

## IX. Um idioma no código, outro na tela
Código, tabelas e URLs em inglês; interface, mensagens e documentos em português via `gettext`.

## X. LGPD por padrão
Só dados reais em produção; desenvolvimento e testes usam dados fictícios gerados por factories.
Segredos ficam em variáveis de ambiente. Dumps de banco nunca entram no repositório.

## Governança
Esta constituição prevalece sobre outras práticas. Emendas exigem PR próprio que atualize a versão
(semver) e os templates afetados.
