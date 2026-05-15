# Fluxo de IA

O prompt principal fica em `app/ai/prompts/review_existing_document.md`.

`AI_MODE=mock` usa apontamentos das regras fixas para simular retorno estruturado.

`AI_MODE=api` usa `OPENAI_API_KEY` e `OPENAI_MODEL`. Se `OPENAI_MODEL` estiver vazio, o sistema usa `DEFAULT_OPENAI_MODEL`. A chamada usa `OPENAI_TIMEOUT`, solicita JSON pela API quando disponível, tenta extrair JSON mesmo se houver texto extra, normaliza campos e evita quebra da aplicação com fallback amigável.

Respostas brutas só são salvas em `storage/ai_raw` quando `SAVE_AI_RAW=true` em desenvolvimento.

## Teste de conectividade

Use:

```bash
python scripts/testar_ia.py
```

Esse script não envia documento real. Ele apenas pede um JSON mínimo para confirmar chave, modelo e conectividade.

## Comparação Mock vs API

Use:

```bash
python scripts/avaliar_revisao.py --mode mock
python scripts/avaliar_revisao.py --mode api
python scripts/avaliar_revisao.py --compare
```

O modo `--compare` roda os PDFs locais em mock e API e gera `comparativo_*.json` em `tests/documentos_referencia/relatorios_avaliacao`.

## Melhorias V2

- O prompt reforça revisão contextual profunda, coerência entre qualificação, cláusulas e assinaturas, erros sutis de gênero, pontuação, concordância e adaptação ruim de modelos.
- O `json_guard` tolera texto antes/depois do JSON, corrige campos ausentes, normaliza tipos/gravidades e remove duplicações internas.
- O merge consolida apontamentos vindos de regras fixas e IA, marcando a fonte como `RULE`, `AI` ou `BOTH`.
- A localização no PDF tenta frase completa, substrings úteis e comparação normalizada sem acentos/espaços múltiplos.
- O modo de avaliação local roda PDFs reais da pasta `tests/documentos_referencia/entrada` e gera métricas em JSON.
- Em falha de API, a sessão fica marcada como `COMPLETED_FALLBACK` e a revisão continua apenas com regras fixas, sem fingir resposta da IA.

## Interpretação dos relatórios de avaliação

- `total_apontamentos`: mede volume, não qualidade sozinho.
- `apontamentos_por_tipo`: mostra onde a revisão está concentrada.
- `apontamentos_por_gravidade`: ajuda a detectar excesso de marcações leves ou falsas críticas.
- `trechos_localizados_pdf`: indica quantos apontamentos conseguiram marcação visual.
- `trechos_nao_localizados_pdf`: deve ser revisado para melhorar prompt, extração ou localização.
- `erros_processamento`: registra falhas sem interromper a avaliação dos demais documentos.
