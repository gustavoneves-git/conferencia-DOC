# Fluxo de IA

O prompt principal fica em `app/ai/prompts/review_existing_document.md`.

`AI_MODE=mock` usa apontamentos das regras fixas para simular retorno estruturado.

`AI_MODE=api` usa `OPENAI_API_KEY` e `OPENAI_MODEL`, exige JSON válido, tenta extrair JSON mesmo se houver texto extra, normaliza campos e evita quebra da aplicação com fallback amigável.

Respostas brutas só são salvas em `storage/ai_raw` quando `SAVE_AI_RAW=true` em desenvolvimento.
