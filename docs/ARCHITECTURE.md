# Arquitetura

A aplicação Flask é organizada por camadas:

- `routes`: entrada HTTP e navegação.
- `services`: fluxo operacional, extração, revisão, exportação e geração.
- `ai`: cliente único de IA, prompts, guard JSON e schemas.
- `repositories`: persistência SQLite.
- `database`: conexão e schema.
- `templates/static`: interface minimalista.

O orquestrador `ReviewOrchestratorService` coordena a V1 sem espalhar responsabilidades entre rotas.
