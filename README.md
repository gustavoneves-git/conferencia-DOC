# Conferência Documento

Plataforma interna da Consiste Contabilidade para conferência operacional de minutas societárias brasileiras com apoio de IA.

## Instalação

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Acesse `http://127.0.0.1:5060`.

## IA

No `.env`, use `AI_MODE=mock` para desenvolvimento local sem chave. Nesse modo, as regras fixas alimentam um retorno estruturado compatível com a camada de IA.

Para usar API:

```env
AI_MODE=api
OPENAI_API_KEY=sua-chave
OPENAI_MODEL=gpt-4.1-mini
SAVE_AI_RAW=false
```

A chave fica somente no `.env`, que é ignorado pelo Git. Todas as chamadas passam por `app/ai/client.py`.

## Fluxo V1

1. Upload de PDF ou DOCX.
2. Extração de texto por página.
3. Classificação documental estimada.
4. Regras fixas iniciais.
5. Revisão por IA mock/API com JSON validado.
6. Consolidação dos apontamentos.
7. PDF grifado quando o original for PDF.
8. Relatório técnico em PDF.
9. DOCX/PDF corrigido para revisão.
10. DOCX/PDF final somente após confirmação humana.

## Observação

O sistema não substitui advogado e não toma decisão jurídica definitiva. Ele é assistente operacional avançado para conferência, produção e padronização documental.
