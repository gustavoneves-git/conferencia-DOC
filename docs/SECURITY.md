# Segurança e LGPD

- `.env` é ignorado pelo Git.
- Bancos SQLite e documentos em `storage` são ignorados.
- A aplicação não registra texto completo sensível no console.
- Resposta bruta da IA é opt-in via `SAVE_AI_RAW=true`.
- Versão final exige confirmação humana.

Documentos reais não devem ser versionados.
