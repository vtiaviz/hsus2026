# Implementation Plan: Autenticação e perfis (M1)

**Spec**: [spec.md](spec.md)

## Technical Context
- Login e logout com as views de `django.contrib.auth`, templates próprios em português.
- Bloqueio por tentativas com `django-axes` (já previsto no plano técnico do PRD): 5 falhas,
  janela de 15 minutos, chave por nome de usuário.
- Perfis = grupos do Django criados por migração de dados.
- Matriz de permissões em `apps/core/permissions.py`: um `TextChoices` `Action` e um dicionário
  `ROLE_ACTIONS` que diz quais ações cada perfil tem. Sem permissões de model do Django: as áreas
  não são models, e a matriz fica legível num só lugar.
- `LoginRequiredMiddleware` do Django 5.1+ para exigir login em tudo; views públicas marcadas com
  `login_not_required`.
- Mixin `ActionRequiredMixin` (CBV) e decorator `action_required` (FBV) para as views de área.
- Barra lateral via context processor que lê a matriz.
- Páginas vazias por área (`reception`, `ambulatory`, `infirmary`, `documents`) só para ter URLs
  reais; cada app nasce aqui com `urls.py` e uma view. O conteúdo vem nas specs seguintes.

## Constitution Check
| Princípio | Como o M1 atende |
| --- | --- |
| I Simplicidade | Uma dependência nova (`django-axes`), justificada pela spec |
| II Testes | Teste parametrizado cobre cada célula da matriz contra a URL da área |
| VII Permissão testada | Padrão negar via middleware + matriz única |
| IX Idioma | Código em inglês, rótulos em português |

## Complexity Tracking
Nenhuma exceção.
