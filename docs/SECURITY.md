# Segurança e LGPD

- `.env` é ignorado pelo Git.
- Bancos SQLite e documentos em `storage` são ignorados.
- A aplicação não registra texto completo sensível no console.
- Resposta bruta da IA é opt-in via `SAVE_AI_RAW=true`.
- Versão final exige confirmação humana.
- `OPENAI_API_KEY` deve ficar somente no `.env`, nunca no código ou em documentação versionada.
- `scripts/testar_ia.py` testa a API sem enviar documento real.
- `scripts/avaliar_revisao.py --mode api` e `--compare` enviam o texto extraído dos PDFs locais para a API. Use apenas com autorização e observância da LGPD.

Documentos reais não devem ser versionados.
